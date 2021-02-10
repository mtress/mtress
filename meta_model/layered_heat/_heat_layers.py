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

from meta_model.physics import celsius_to_kelvin


class HeatLayers:
    def __init__(self,
                 energy_system,
                 temperature_levels,
                 reference_temperature):
        """
        :param energy_system: solph.EnergySystem
        :param temperature_levels: list [temperature]
        :param reference_temperature: reference temperature for energy (°C)
        """
        # Create object collections for temperature dependent technologies
        self.energy_system = energy_system
        self.b_th = dict()
        self.b_th_in = dict()
        self.TEMPERATURE_LEVELS = temperature_levels
        self.REFERENCE_TEMPERATURE = reference_temperature

        temp_low = None
        for temperature in temperature_levels:
            # Naming of new temperature bus
            temperature_str = "{0:.0f}".format(temperature)
            b_th_label = 'b_th_' + temperature_str
            b_th_in_label = 'b_th_in_' + temperature_str

            ################################################################
            # Thermal buses
            b_th_level = solph.Bus(label=b_th_label)

            if temp_low is None:
                b_th_in_level = solph.Bus(label=b_th_in_label,
                                          outputs={b_th_level: solph.Flow()})
                self.b_th_lowest = b_th_level
            else:
                b_th_in_level = solph.Bus(
                    label=b_th_in_label,
                    outputs={self.b_th_in[temp_low]: solph.Flow(),
                             b_th_level: solph.Flow()})

            self.b_th[temperature] = b_th_level
            self.b_th_in[temperature] = b_th_in_level

            energy_system.add(b_th_level, b_th_in_level)

            ################################################################
            # Temperature risers
            if temp_low is not None:
                temp_low_str = "{0:.0f}".format(temp_low)
                temp_high_str = "{0:.0f}".format(temperature)
                heater_label = 'rise_' + temp_low_str + '_' + temp_high_str
                heater_ratio = ((celsius_to_kelvin(temp_low)
                                 - self.REFERENCE_TEMPERATURE)
                                / (celsius_to_kelvin(temperature)
                                   - self.REFERENCE_TEMPERATURE))
                heater = solph.Transformer(
                    label=heater_label,
                    inputs={b_th_in_level: solph.Flow(),
                            self.b_th[temp_low]: solph.Flow()},
                    outputs={b_th_level: solph.Flow()},
                    conversion_factors={
                        b_th_in_level: 1 - heater_ratio,
                        self.b_th[temp_low]: heater_ratio,
                        b_th_level: 1})

                energy_system.add(heater)

            # prepare for next iteration of the loop
            temp_low = temperature
