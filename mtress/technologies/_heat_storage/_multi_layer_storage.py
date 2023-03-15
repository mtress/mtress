# -*- coding: utf-8 -*-

"""
Storage that has multiple heat layers that are all accessible at all times.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

SPDX-License-Identifier: MIT
"""
from oemof.solph import Flow
from oemof.solph.components import GenericStorage
from oemof.solph.constraints import shared_limit
from oemof.thermal import stratified_thermal_storage

from mtress._data_handler import TimeseriesSpecifier
from mtress.carriers import Heat
from mtress.physics import H2O_DENSITY, H2O_HEAT_CAPACITY, kJ_to_MWh

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
        ambient_temperature: TimeseriesSpecifier,
        u_value: float | None = None,
    ):
        """
        Create layered heat storage component.

        :param diameter: Diameter of the storage in m
        :param volume: Volume of the storage in m³
        :param u_value: Thermal transmittance in W/m²/K
        :param ambient_temperature: Ambient temperature in deg C
        """
        super().__init__(
            name=name,
            diameter=diameter,
            volume=volume,
            ambient_temperature=ambient_temperature,
            u_value=u_value
        )
        
        # Solph specific params
        # Bookkeeping of oemof components
        self.storage_components = {}

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        # Create storage components according to the temperature levels defined
        # by the heat carrier object
        heat_carrier = self.location.get_carrier(Heat)
        temperature_levels = heat_carrier.temperature_levels
        reference_temperature = heat_carrier.reference_temperature

        for temperature in temperature_levels:
            bus = heat_carrier.outputs[temperature]

            capacity = self.volume * kJ_to_MWh(
                (temperature - reference_temperature) * H2O_DENSITY * H2O_HEAT_CAPACITY
            )

            if self.u_value is None:
                loss_rate = 0
                fixed_losses_relative = 0
                fixed_losses_absolute = 0
            else:
                (
                    loss_rate,
                    fixed_losses_relative,
                    fixed_losses_absolute,
                ) = stratified_thermal_storage.calculate_losses(
                    u_value=self.u_value,
                    diameter=self.diameter,
                    temp_h=temperature,
                    temp_c=reference_temperature,
                    temp_env=self._solph_model.data.get_timeseries(
                        self.ambient_temperature
                    ),
                )

            # losses to the upper side of the storage will just leave the
            # storage for the uppermost level.
            # So, we neglect them for the others.
            if temperature != max(temperature_levels):
                fixed_losses_relative = fixed_losses_absolute = 0

            storage = self._solph_model.add_solph_component(
                mtress_component=self,
                label=f"{temperature:.0f}",
                solph_component=GenericStorage,
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
        reference_temperature = self.location.get_carrier(Heat).reference_temperature

        components, weights = zip(
            *[
                (
                    component,
                    1
                    / kJ_to_MWh(
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
            limit_name=self._solph_model.get_label(self, "storage_limit"),
            components=components,
            weights=weights,
            upper_limit=self.volume,
        )
