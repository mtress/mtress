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


class HeatLayers:
    """
    Connector class for modeling power flows with variable temperature levels,
    see https://arxiv.org/abs/2012.12664

      Layer Inputs        Layers Outputs

      (Qin(T3))           (Q(T3))
          │   ↘           ↗
          │    [heater2,3]
          ↓               ↖
      (Qin(T2))           (Q(T2))
          │    ↘          ↗
          │    [heater1,2]
          ↓               ↖
      (Qin(T1))---------->(Q(T1))

    Heat sources connect to the Qin for the corresponding temperatures.
    If efficiency increases with lower temperature,
    techs should connect to all input nodes (see e.g. LayeredHeatPump).
    Note that there are also heat supply techs with constant efficiency.
    Those only need to connect to the hottest layer.
    """

    def __init__(self,
                 energy_system,
                 temperature_levels,
                 reference_temperature,
                 label=''):
        """
        :param energy_system: solph.EnergySystem
        :param temperature_levels: list [temperature]
        :param reference_temperature: reference temperature for energy (°C)
        """

        # Create object collections for temperature dependent technologies
        self.energy_system = energy_system
        self.b_th = dict()
        self.b_th_in = dict()
        # keep only unique values
        if reference_temperature in temperature_levels:
            temperature_levels.remove(reference_temperature)
        temperature_levels = list(set(temperature_levels))
        temperature_levels.sort()
        self._temperature_levels = temperature_levels
        self._reference_temperature = reference_temperature

        error_msg = "Reference temperature needs to be the lowest one."

        assert reference_temperature < temperature_levels[0], error_msg

        if len(label) > 0:
            label = label + '_'

        temp_low = None
        for temperature in self._temperature_levels:
            # Naming of new temperature bus
            temperature_str = "{0:.0f}".format(temperature)
            b_th_label = label + 'b_th_' + temperature_str
            b_th_in_label = label + 'b_th_in_' + temperature_str

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
            self.b_th_in_highest = b_th_in_level

            self.b_th[temperature] = b_th_level
            self.b_th_in[temperature] = b_th_in_level

            energy_system.add(b_th_level, b_th_in_level)

            ################################################################
            # Temperature risers
            if temp_low is not None:
                temp_low_str = "{0:.0f}".format(temp_low)
                temp_high_str = "{0:.0f}".format(temperature)
                heater_label = (label
                                + 'rise_' + temp_low_str
                                + '_' + temp_high_str)
                heater_ratio = ((temp_low - self._reference_temperature)
                                / (temperature - self._reference_temperature))
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

    @property
    def temperature_levels(self):
        """
        :return: list of temperature levels (in K)
        """
        return self._temperature_levels

    @property
    def reference_temperature(self):
        """
        :return: reference temperature (in K)
        """
        return self._reference_temperature
