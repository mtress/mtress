# -*- coding: utf-8 -*-

"""
Basic heat layer functionality.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""
from oemof import solph, thermal

from ..carriers import Heat
from ..physics import H2O_DENSITY, H2O_HEAT_CAPACITY, kJ_to_MWh
from ._abstract_technology import AbstractTechnology

# Thermal conductivity of insulation material
TC_INSULATION = 0.04  # W / (m * K)


class HeatStorage(AbstractTechnology):
    """
    Layered heat storage.

    Matrjoschka storage, i.e.one storage per temperature levels with shared resources.
    See https://arxiv.org/abs/2012.12664
    """

    def __init__(
        self,
        diameter: float,
        volume: float,
        insulation_thickness: float,
        ambient_temperature: float | str,
        **kwargs,
    ):
        """
        Create layered heat storage component.

        :param diameter: Diameter of the storage in m
        :param volume: Volume of the storage in m³
        :param insulation_thickness: Insulation thickness in m
        :param ambient_temperature: Ambient temperature in deg C
        """
        super().__init__(**kwargs)

        # Bookkeeping of oemof components
        self._storage_components = {}

        # Create storage components according to the temperature levels defined
        # by the heat carrier object
        heat_carrier = self.location.get_carrier(Heat)
        self._temperature_levels = heat_carrier.temperature_levels
        self._reference_temperature = heat_carrier.reference_temperature

        # General parameters of the storage
        self.volume = volume
        self.insulation_thickness = insulation_thickness

        for temperature in self._temperature_levels:
            bus = heat_carrier.outputs[temperature]

            capacity = self.volume * kJ_to_MWh(
                (temperature - self._reference_temperature)
                * H2O_DENSITY
                * H2O_HEAT_CAPACITY
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
                ) = thermal.stratified_thermal_storage.calculate_losses(
                    u_value=TC_INSULATION / self.insulation_thickness,
                    diameter=diameter,
                    temp_h=temperature,
                    temp_c=self._reference_temperature,
                    temp_env=ambient_temperature,
                )

            # losses to the upper side of the storage will just leave the
            # storage for the uppermost level.
            # So, we neglect them for the others.
            if temperature != max(self._temperature_levels):
                fixed_losses_relative = fixed_losses_absolute = 0

            storage = solph.GenericStorage(
                label=self._generate_label(f"st_{temperature:.0f}"),
                inputs={bus: solph.Flow()},
                outputs={bus: solph.Flow()},
                nominal_storage_capacity=capacity,
                loss_rate=loss_rate,
                fixed_losses_absolute=fixed_losses_absolute,
                fixed_losses_relative=fixed_losses_relative,
            )

            self._storage_components[temperature] = storage
            self.location.energy_system.add(storage)

    def add_constraints(self, model: solph.Model):
        """Add constraints to the model."""
        components, weights = zip(
            *[
                (
                    component,
                    1
                    / kJ_to_MWh(
                        H2O_HEAT_CAPACITY
                        * H2O_DENSITY
                        * (temperature - self._reference_temperature)
                    ),
                )
                for temperature, component in self._storage_components.items()
            ]
        )

        solph.constraints.shared_limit(
            model=model,
            quantity=model.GenericStorageBlock.storage_content,
            limit_name=self._generate_label("storage_limit"),
            components=components,
            weights=weights,
            upper_limit=self.volume,
        )
