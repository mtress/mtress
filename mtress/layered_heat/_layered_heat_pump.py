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

from mtress.physics import (calc_cop,
                            celsius_to_kelvin)


class LayeredHeatPump:
    """
    Clustered heat pump for modeling power flows
    with variable temperature levels.
    Connects any input to any output using solph.Transformer
    with shared resources, see https://arxiv.org/abs/2012.12664

Basics of the MTRESS model

    Resources      Technologies

        (E)--------->[Rod]
                                          Flows:
                ─────────────────          E --> Rod, E --> HP2, E --> HP1, E --> HP0
               │                │          A --> HP2, A --> HP1, A --> HP0
               │     [HP2]      │          1HP --> HP2, 1HP --> HP1, 1HP -->HP0
        (A)    │                │
               │      [HP1]     │
               │                │
               │(1HP) [HP0]     │
                ─────────────────

    """

    def __init__(self,
                 energy_system,
                 heat_layers,
                 electricity_source,
                 heat_sources,
                 thermal_power_limit=None,
                 cop_0_35=4.6,
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

        heat_budget_split = solph.Bus(label=label+"heat_budget_split")
        if thermal_power_limit:
            heat_budget = solph.Source(
                label=label+"heat_budget",
                outputs={
                    heat_budget_split: solph.Flow(
                        nominal_value=thermal_power_limit)})
        else:
            heat_budget = solph.Source(
                label=label+"heat_budget",
                outputs={
                    heat_budget_split: solph.Flow()})

        self.heat_budget_flow = (heat_budget.label,
                                 heat_budget_split.label)

        energy_system.add(electricity_bus, heat_budget_split, heat_budget)

        for source in heat_sources:
            temperature_lower = heat_sources[source]
            heat_source = solph.Bus(
                label=label+"in_"+source)
            self.b_th_in[source] = heat_source
            energy_system.add(heat_source)

            for target_temperature in heat_layers.temperature_levels:
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
                        electricity_bus: solph.Flow(),
                        heat_budget_split: solph.Flow()},
                    outputs={
                        heat_layers.b_th_in[target_temperature]: solph.Flow()},
                    conversion_factors={
                        heat_source: (cop-1) / cop,
                        electricity_bus: 1/cop,
                        heat_layers.b_th_in[target_temperature]: 1})

                energy_system.add(heat_pump_level)

    def heat_output(self, results_dict):
        """
        Total energy
        """
        return results_dict[self.heat_budget_flow]['sequences']['flow']
