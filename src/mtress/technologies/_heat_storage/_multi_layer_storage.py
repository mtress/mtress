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
from mtress.physics import mega_to_one

from ._abstract_heat_storage import AbstractHeatStorage


class LayeredHeatStorage(AbstractHeatStorage):
    """
    Layered heat storage.

    Matrjoschka storage, i.e. one storage per temperature level
    with shared resources.
    See https://arxiv.org/abs/2012.12664
    """

    def __init__(
        self,
        name: str,
        diameter: float,
        volume: float,
        power_limit: float,
        ambient_temperature: TimeseriesSpecifier,
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
        # Create storage components according to the temperature levels defined
        # by the heat carrier object

        heat_carrier = self.location.get_carrier(HeatCarrier)
        reference_temperature = heat_carrier.reference

        temperature_levels = heat_carrier.levels

        loss_flow = {}

        for temperature in temperature_levels:
            if self.min_temperature <= temperature <= self.max_temperature:
                level_node = heat_carrier.level_nodes[temperature]

                if temperature in self.initial_storage_levels:
                    initial_storage_level = self.initial_storage_levels[
                        temperature
                    ]
                else:
                    initial_storage_level = None

                if self.u_value is None:
                    loss_rate = 0
                    fixed_losses_relative = 0
                    fixed_losses_absolute = 0
                else:
                    (
                        loss_rate,
                        fixed_losses_relative,
                        fixed_losses_absolute,  # MW
                    ) = stratified_thermal_storage.calculate_losses(
                        u_value=self.u_value,
                        diameter=self.diameter,
                        temp_h=temperature,
                        temp_c=reference_temperature,
                        temp_env=self._solph_model.data.get_timeseries(
                            self.ambient_temperature,
                            kind=TimeseriesType.INTERVAL,
                        ),
                    )
                    fixed_losses_relative = fixed_losses_relative
                    fixed_losses_absolute = mega_to_one(fixed_losses_absolute)

                # losses to the upper side of the storage will just leave the
                # storage for the uppermost level.
                # So, we neglect them for the others.
                if temperature != max(temperature_levels):
                    fixed_losses_relative = fixed_losses_absolute = 0

                bus = self.create_solph_node(
                    label=f"b_{temperature:.0f}",
                    node_type=Bus,
                    inputs={level_node: Flow(nominal_value=self.power_limit)},
                    outputs={level_node: Flow(nominal_value=self.power_limit)}
                    | loss_flow,
                )

                self.buses[temperature] = bus

                storage = self.create_solph_node(
                    label=f"{temperature:.0f}",
                    node_type=GenericStorage,
                    inputs={bus: Flow()},
                    outputs={bus: Flow()},
                    nominal_storage_capacity=1e3 * self.volume,  # liters
                    loss_rate=loss_rate,
                    balanced=self.balanced,
                    initial_storage_level=initial_storage_level,
                    fixed_losses_absolute=fixed_losses_absolute,
                    fixed_losses_relative=fixed_losses_relative,
                )

                self.storage_components[temperature] = storage

                loss_flow = {bus: Flow(bidirectional=True)}

    def add_constraints(self):
        """Add constraints to the model."""
        model = self._solph_model.model

        # >= && <= should be replaced by ==
        shared_limit(
            model=model,
            quantity=model.GenericStorageBlock.storage_content,
            limit_name=str(self.create_label("storage_limit")),
            components=self.storage_components.values(),
            weights=1e3,
            upper_limit=self.volume,
            lower_limit=self.volume,
        )

        temperatures = list(self.storage_components.keys())

        # When a storage loses energy, in reality it will not direktly go
        # to the lowest temperature. We mimic this by (additional) step-wise
        # downshifting of the remaining heat.
        for lower_temperature, upper_temperature in zip(
            temperatures, temperatures[1:]
        ):
            def equate_variables_rule(_, t):
                ratio = (lower_temperature - self.ambient_temperature[t]) / (
                    upper_temperature - self.ambient_temperature[t]
                )
                return (
                    (ratio / (1 - ratio))
                    * (
                        model.GenericStorageBlock.storage_losses[
                            self.storage_components[upper_temperature], t
                        ]
                    )
                ) <= model.flow[
                    self.buses[upper_temperature],
                    self.buses[lower_temperature],
                    t,
                ]

            setattr(
                model,
                str(self.create_label(f"losses_{upper_temperature}")),
                po.Constraint(model.TIMESTEPS, rule=equate_variables_rule),
            )
