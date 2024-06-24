# -*- coding: utf-8 -*-

"""
Storage that has multiple heat layers that are all accessible at all times.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

SPDX-License-Identifier: MIT
"""

from numpy import power
from oemof.solph import Flow
from oemof.solph.components import GenericStorage
from oemof.solph.constraints import shared_limit
from oemof.thermal import stratified_thermal_storage

from mtress._data_handler import TimeseriesSpecifier, TimeseriesType
from mtress.carriers import HeatCarrier
from mtress.physics import H2O_DENSITY, H2O_HEAT_CAPACITY, SECONDS_PER_HOUR, mega_to_one

from ._abstract_heat_storage import AbstractHeatStorage


class LayeredHeatStorage(AbstractHeatStorage):
    """
    Layered heat storage.

    Matrjoschka storage, i.e. one storage per temperature level with shared resources.
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

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        # Create storage components according to the temperature levels defined
        # by the heat carrier object

        heat_carrier = self.location.get_carrier(HeatCarrier)
        reference_temperature = heat_carrier.reference

        temperature_levels = heat_carrier.levels

        for temperature in temperature_levels:
            if self.min_temperature <= temperature <= self.max_temperature:
                bus = heat_carrier.level_nodes[temperature]

                capacity = (
                    self.volume
                    * (
                        (temperature - reference_temperature)
                        * H2O_DENSITY
                        * H2O_HEAT_CAPACITY
                    )
                    / SECONDS_PER_HOUR
                )
                if self.u_value is None:
                    loss_rate = 0
                    fixed_losses_relative = 0
                    fixed_losses_absolute = 0
                else:
                    (
                        loss_rate,
                        fixed_losses_relative,  # MW
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
                    fixed_losses_relative = mega_to_one(fixed_losses_relative)
                    fixed_losses_absolute = mega_to_one(fixed_losses_absolute)

                # losses to the upper side of the storage will just leave the
                # storage for the uppermost level.
                # So, we neglect them for the others.
                if temperature != max(temperature_levels):
                    fixed_losses_relative = fixed_losses_absolute = 0

                storage = self.create_solph_node(
                    label=f"{temperature:.0f}",
                    node_type=GenericStorage,
                    inputs={bus: Flow()},
                    outputs={bus: Flow()},
                    nominal_storage_capacity=capacity,
                    loss_rate=loss_rate,
                    fixed_losses_absolute=fixed_losses_absolute,
                    fixed_losses_relative=fixed_losses_relative,
                )

                self.storage_components[temperature] = storage

    def add_constraints(self):
        """Add constraints to the model."""
        reference_temperature = self.location.get_carrier(HeatCarrier).reference

        components, weights = zip(
            *[
                (
                    component,
                    SECONDS_PER_HOUR
                    / (
                        H2O_HEAT_CAPACITY
                        * H2O_DENSITY
                        * (temperature - reference_temperature)
                    ),
                )
                for temperature, component in self.storage_components.items()
            ]
        )

        shared_limit(
            model=self._solph_model.model,
            quantity=self._solph_model.model.GenericStorageBlock.storage_content,
            limit_name=str(self.create_label("storage_limit")),
            components=components,
            weights=weights,
            upper_limit=self.volume,
        )
