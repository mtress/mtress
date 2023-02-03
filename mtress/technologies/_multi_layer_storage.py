# -*- coding: utf-8 -*-

"""
Basic heat layer functionality.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""
from oemof.solph import Flow
from oemof.solph.components import GenericStorage
from oemof.solph.constraints import shared_limit
from oemof.thermal import stratified_thermal_storage

from .._abstract_component import AbstractSolphComponent
from .._data_handler import TimeseriesSpecifier
from ..carriers import Heat
from ..physics import H2O_DENSITY, H2O_HEAT_CAPACITY, kJ_to_MWh
from ._abstract_technology import AbstractTechnology

# Thermal conductivity of insulation material
TC_INSULATION = 0.04  # W / (m * K)


class LayeredHeatStorage(AbstractTechnology, AbstractSolphComponent):
    """
    Layered heat storage.

    Matrjoschka storage, i.e.one storage per temperature levels with shared resources.
    See https://arxiv.org/abs/2012.12664
    """

    def __init__(
        self,
        name: str,
        diameter: float,
        volume: float,
        insulation_thickness: float,
        ambient_temperature: TimeseriesSpecifier,
    ):
        """
        Create layered heat storage component.

        :param diameter: Diameter of the storage in m
        :param volume: Volume of the storage in m³
        :param insulation_thickness: Insulation thickness in m
        :param ambient_temperature: Ambient temperature in deg C
        """
        super().__init__(name)

        # General parameters of the storage
        self.diameter = diameter
        self.volume = volume
        self.insulation_thickness = insulation_thickness
        self.ambient_temperature = ambient_temperature

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

            if self.insulation_thickness <= 0:
                loss_rate = 0
                fixed_losses_relative = 0
                fixed_losses_absolute = 0
            else:
                (
                    loss_rate,
                    fixed_losses_relative,
                    fixed_losses_absolute,
                ) = stratified_thermal_storage.calculate_losses(
                    u_value=TC_INSULATION / self.insulation_thickness,
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


class MixedHeatStorage(AbstractTechnology, AbstractSolphComponent):
    def __init__(self, name: str):
        super().__init__(name)
