# -*- coding: utf-8 -*-

"""
basic heat layer functionality

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""

from oemof import solph
from oemof import thermal

from meta_model.physics import (celsius_to_kelvin, kilo_to_mega, kJ_to_MWh,
                                H2O_DENSITY, H2O_HEAT_CAPACITY,
                                TC_INSULATION)


class MultiLayerStorage:
    def __init__(self,
                 diameter,
                 volume,
                 insulation_thickness,
                 ambient_temperature,
                 heat_layers):
        """
        :param diameter: numeric scalar (in m)
        :param volume: numeric scalar (in m³)
        :param ambient_temperature: numeric scalar or sequence (in °C)
        :param heat_layers: HeatLayers object
        """
        self._h_storage_comp = list()

        self.energy_system = heat_layers.energy_system
        self._temperature_levels = heat_layers.TEMPERATURE_LEVELS
        self._reference_temperature = heat_layers.REFERENCE_TEMPERATURE

        self.heat_storage_volume = volume

        self._heat_storage_insulation = insulation_thickness

        for temperature in self._temperature_levels:
            temperature_str = "{0:.0f}".format(temperature)
            storage_label = 's_heat_' + temperature_str
            b_th_level = heat_layers.b_th[temperature]

            hs_capacity = self.heat_storage_volume * \
                          kJ_to_MWh((celsius_to_kelvin(temperature)
                                     - heat_layers.REFERENCE_TEMPERATURE) *
                                    H2O_DENSITY *
                                    H2O_HEAT_CAPACITY)

            if self._heat_storage_insulation <= 0:
                hs_loss_rate = 0
                hs_fixed_losses_relative = 0
                hs_fixed_losses_absolute = 0
            else:
                (hs_loss_rate,
                 hs_fixed_losses_relative,
                 hs_fixed_losses_absolute) = (
                    thermal.stratified_thermal_storage.calculate_losses(
                        u_value=TC_INSULATION / self._heat_storage_insulation,
                        diameter=diameter,
                        temp_h=temperature,
                        temp_c=self.REFERENCE_TEMPERATURE,
                        temp_env=ambient_temperature))

            s_heat = solph.GenericStorage(
                label=storage_label,
                inputs={b_th_level: solph.Flow()},
                outputs={b_th_level: solph.Flow()},
                nominal_storage_capacity=hs_capacity,
                loss_rate=hs_loss_rate,
                fixed_losses_absolute=hs_fixed_losses_absolute,
                fixed_losses_relative=hs_fixed_losses_relative
            )

            self._h_storage_comp.append(s_heat)
            self.energy_system.add(s_heat)

    def add_shared_limit(self, model):
        """
        :param model: solph.model
        """
        w_factor = [1 / kilo_to_mega(H2O_HEAT_CAPACITY
                                     * H2O_DENSITY
                                     * (celsius_to_kelvin(temp)
                                        - self._reference_temperature))
                    for temp in self._temperature_levels]

        solph.constraints.shared_limit(
            model, model.GenericStorageBlock.storage_content,
            'storage_limit', self._h_storage_comp, w_factor,
            upper_limit=self.heat_storage_volume)

    @property
    def TEMPERATURE_LEVELS(self):
        return self._temperature_levels

    @property
    def HEAT_STORAGE_INSULATION(self):
        return self._heat_storage_insulation

    @property
    def REFERENCE_TEMPERATURE(self):
        return self._reference_temperature
