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
                 heat_sources,
                 cop_0_35=4.7,
                 label=""):
        """
        :param energy_system:
        :param heat_layers:
        :param electricity_source:
        :param heat_sources:
        :param cop_0_35:
        :param label:
        """
        self.b_th_in = dict()
        self.cop = dict()
        self.heat_out_flows = list()

        if len(label) > 0:
            label = label + "_"

        electricity_bus = solph.Bus(label=label+"heat_pump_electricity",
                                    inputs={electricity_source: solph.Flow()})

        energy_system.add(electricity_bus)

        for source in heat_sources:
            temperature_lower = heat_sources[source]
            heat_source = solph.Bus(
                label=label+"in_"+source)
            self.b_th_in[source] = heat_source
            energy_system.add(heat_source)

            for target_temperature in heat_layers.TEMPERATURE_LEVELS:
                temperature_higher_str = "{0:.0f}".format(target_temperature)
                hp_str = label+source+"_"+temperature_higher_str

                cop = calc_cop(
                    temp_input_high=celsius_to_kelvin(temperature_lower),
                    temp_output_high=celsius_to_kelvin(target_temperature),
                    cop_0_35=cop_0_35)

                self.cop[(source, target_temperature)] = cop

                heat_pump_level = solph.Transformer(
                    label=hp_str,
                    inputs={
                        heat_source: solph.Flow(),
                        electricity_bus: solph.Flow()},
                    outputs={
                        heat_layers.b_th_in[target_temperature]: solph.Flow()},
                    conversion_factors={
                        heat_source: (cop-1) / cop,
                        electricity_bus: 1/cop,
                        heat_layers.b_th_in[target_temperature]: 1})

                energy_system.add(heat_pump_level)
                self.heat_out_flows.append(
                    (heat_pump_level.label,
                     heat_layers.b_th_in[target_temperature].label()))

    def heat_output(self, results_dict):
        """
        Total energy
        """

        e_hp_th = 0
        for flow in self.heat_out_flows:
            the_flow = results_dict[flow]['sequences']['flow']
            e_hp_th += the_flow
