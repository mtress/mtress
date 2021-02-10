# -*- coding: utf-8 -*-

"""
heat pump to be used with HeatLayer

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""

from oemof import solph

from meta_model.physics import (calc_cop,
                                celsius_to_kelvin)


class LayeredHeatPump:
    def __init__(self,
                 energy_system,
                 heat_layers,
                 electricity_source,
                 temperature_levels_primary,
                 temperature_levels_secondary,
                 cop_0_35=4.7,
                 label=""):
        """
        :param energy_system:
        :param heat_layers:
        :param temperature_levels_primary:
        :param temperature_levels_secondary:
        """
        self.b_th_in = dict()
        self.cop = dict()

        if len(label) > 0:
            label = label + "_"

        electricity_bus = solph.Bus(label=label+"heat_pump_electricity",
                                    inputs={electricity_source: solph.Flow()})

        energy_system.add(electricity_bus)

        for temperature_lower in temperature_levels_primary:
            temperature_lower_str = "{0:.0f}".format(temperature_lower)
            heat_source = solph.Bus(
                label=label+"in_"+temperature_lower_str)
            self.b_th_in[temperature_lower] = heat_source
            energy_system.add(heat_source)

            for temperature_higher in temperature_levels_secondary:
                temperature_higher_str = "{0:.0f}".format(temperature_higher)
                hp_str = label+temperature_lower_str+"_"+temperature_higher_str

                cop = calc_cop(
                    temp_input_high=celsius_to_kelvin(temperature_lower),
                    temp_output_high=celsius_to_kelvin(temperature_higher),
                    cop_0_35=cop_0_35)

                self.cop[(temperature_lower, temperature_higher)] = cop

                heat_pump_level = solph.Transformer(
                    label=hp_str,
                    inputs={
                        heat_source: solph.Flow(),
                        electricity_bus: solph.Flow()},
                    outputs={
                        heat_layers.b_th_in[temperature_higher]: solph.Flow()},
                    conversion_factors={
                        heat_source: (cop-1) / cop,
                        electricity_bus: 1/cop,
                        heat_layers.b_th_in[temperature_higher]: 1})

                energy_system.add(heat_pump_level)
