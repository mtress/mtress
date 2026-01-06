# -*- coding: utf-8 -*-

"""
Storage that has multiple heat layers that are all accessible at all times.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

SPDX-License-Identifier: MIT
"""

from oemof.solph import Bus, Flow
from oemof.solph.components import GenericStorage
from oemof.solph.constraints import shared_limit
from oemof.thermal import stratified_thermal_storage
from pyomo import environ as po

from mtress._data_handler import TimeseriesSpecifier, TimeseriesType
from mtress.carriers import HeatCarrier
from mtress.physics import H2O_DENSITY, H2O_HEAT_CAPACITY, SECONDS_PER_HOUR

from ._abstract_heat_storage import AbstractHeatStorage

from ..._constants import EnergyType


class LayeredHeatStorage(AbstractHeatStorage):
    """
    Layered heat storage.

    Layered storage, i.e. one subvolume per temperature level
    following https://doi.org/10.1016/j.apenergy.2022.118890.

    For simplification, an infitesimal subvolume for each temperature is
    and will be assumed to be always present, meaning that losses do not skip
    depleted layers and top-level losses will always consider the highest
    temeprature.
    Note that currently, only heat losses through the side are implemented,
    the storage only works for min_temperature == ambient_temperature.
    """

    def __init__(
        self,
        name: str,
        diameter: float,
        volume: float,
        power_limit: float,
        ambient_temperature: float,
        u_value: float | None = None,
        max_temperature: float | None = None,
        min_temperature: float | None = None,
        balanced: bool = True,
        initial_storage_levels: dict | None = None,
    ):
        """
        Create layered heat storage component.

        :param diameter: Diameter of the storage in m
        :param volume: Volume of the storage in m³
        :param power_limit: power in W
        :param ambient_temperature: Ambient temperature in °C
        :param reference_temperature: Reference temperature in °C
        :param u_value: Thermal transmittance in W/m²/K
        """
        super().__init__(
            name=name,
            diameter=diameter,
            volume=volume,
            power_limit=power_limit,
            ambient_temperature=ambient_temperature,
            u_value=u_value,
            max_temperature=max_temperature,
            min_temperature=min_temperature,
        )

        # Solph specific params
        # Bookkeeping of oemof components
        self.storage_components = {}
        self.buses = {}

        self.balanced = balanced
        if initial_storage_levels is None:
            initial_storage_levels = {}

        self.initial_storage_levels = initial_storage_levels

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        # Create storage components according to the temperature levels defined
        # by the heat carrier object

        heat_carrier = self.location.get_carrier(HeatCarrier)

        temperature_levels = heat_carrier.levels

        gain_flow = {}

        for temperature in temperature_levels:
            if self.min_temperature <= temperature <= self.max_temperature:
                level_node = heat_carrier.level_nodes[temperature]

                if temperature in self.initial_storage_levels:
                    initial_storage_level = self.initial_storage_levels[
                        temperature
                    ]
                else:
                    initial_storage_level = None

                bus = self.create_solph_node(
                    label=f"b_{temperature:.0f}",
                    node_type=Bus,
                    inputs={
                        level_node: Flow(
                            custom_properties={
                                "unit": "kg/h",
                                "energy_type": EnergyType.HEAT,
                            },
                            nominal_value=self.power_limit,
                        )
                    },
                    outputs={
                        level_node: Flow(
                            custom_properties={
                                "unit": "kg/h",
                                "energy_type": EnergyType.HEAT,
                            },
                            nominal_value=self.power_limit,
                        )
                    }
                    | gain_flow,
                )

                self.buses[temperature] = bus

                storage = self.create_solph_node(
                    label=f"{temperature:.0f}",
                    node_type=GenericStorage,
                    inputs={
                        bus: Flow(
                            custom_properties={
                                "unit": "kg/h",
                                "energy_type": EnergyType.HEAT,
                            }
                        )
                    },
                    outputs={
                        bus: Flow(
                            custom_properties={
                                "unit": "kg/h",
                                "energy_type": EnergyType.HEAT,
                            }
                        )
                    },
                    nominal_storage_capacity=self.volume * H2O_DENSITY,
                    balanced=self.balanced,
                    initial_storage_level=initial_storage_level,
                )

                self.storage_components[temperature] = storage

                if self.u_value is not None:
                    gain_flow = {
                        bus: Flow(
                            custom_properties={
                                "unit": "kg/h",
                                "energy_type": EnergyType.HEAT,
                            }
                        )
                    }

    def add_constraints(self):
        """Add constraints to the model."""
        model = self._solph_model.model

        # >= && <= should be replaced by ==
        shared_limit(
            model=model,
            quantity=model.GenericStorageBlock.storage_content,
            limit_name=f"{self.node.label}_storage_limit",
            components=self.storage_components.values(),
            weights=len(self.storage_components) * [1],
            upper_limit=self.volume * H2O_DENSITY,
            lower_limit=self.volume * H2O_DENSITY,
        )

        if self.u_value is not None:
            temperatures = list(self.storage_components.keys())

            # When a storage loses energy, in reality it will not direktly go
            # to the lowest temperature. We mimic this by (additional)
            # step-wise downshifting of the remaining heat.
            for lower_temperature, upper_temperature in zip(
                temperatures, temperatures[1:]
            ):

                loss_rate, _, fixed_losses = (
                    stratified_thermal_storage.calculate_losses(
                        self.u_value,
                        self.diameter,
                        upper_temperature,
                        lower_temperature,
                        self.ambient_temperature,
                    )
                )
                # fixed losses are only present for the top level
                if upper_temperature < temperatures[-1]:
                    fixed_losses = 0

                def equate_variables_rule(_, t):
                    return (
                        fixed_losses
                        + loss_rate
                        * (
                            model.GenericStorageBlock.storage_content[
                                self.storage_components[upper_temperature], t
                            ]
                        )
                    ) == model.flow[
                        self.buses[upper_temperature],
                        self.buses[lower_temperature],
                        t,
                    ]

                setattr(
                    model,
                    f"{self.node.label}_losses_{upper_temperature}",
                    po.Constraint(model.TIMESTEPS, rule=equate_variables_rule),
                )
