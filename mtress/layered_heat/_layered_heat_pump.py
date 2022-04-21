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

    Flows:
    E --> HP1,         E --> HP2,       E --> HP3
    A --> HP1,         A --> HP2,       A --> HP3
    1HP --> HP1,     1HP --> HP2,     1HP --> HP3
    HP0 --> Qin(T1), HP1 --> Qin(T2), HP2 --> Qin(T3)

    Sketch:
        Resources     | Technologies |  Layer Inputs

               ┏━━━━━━━━━━━━━━┓
         ┌─────╂───────→[HP3]─╂────────→(Qin(T3))
         │     ┃  ┌─────↗     ┃            ↓
       (E,A)───╂──┼────→[HP2]─╂────────→(Qin(T2))
         │     ┃  │┌─────↗    ┃            ↓
         └─────╂──┼┼───→[HP1]─╂────────→(Qin(T1))
               ┃ [1HP]────↗   ┃
               ┗━━━━━━━━━━━━━━┛

    The heat pump is modelled as an array of virtual heat pumps,
    each with the correct COP for the corresponding temperatures.
    To not allow producing more heat then the real heat pump,
    all these virtual heat pumps share anergy and energy sources
    and can further have one shared virtual normalisation source (1HP).
    """
    def __init__(self,
                 heat_layers,
                 electricity_source,
                 heat_sources,
                 thermal_power_limit=None,
                 cop_0_35=4.6,
                 label=""):
        """
        :param heat_layers: HeatLayers object to attach to
        :param electricity_source:
        :param heat_sources:
        :param cop_0_35:
        :param label:
        """
        self.b_th_in = dict()
        self.cop = dict()
        self.heat_out_flows = list()

        energy_system = heat_layers.energy_system

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
                    temp_input=celsius_to_kelvin(temperature_lower),
                    temp_output=celsius_to_kelvin(target_temperature),
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

                self.heat_out_flows.append((
                    heat_pump_level.label,
                    heat_layers.b_th_in[target_temperature].label))

                energy_system.add(heat_pump_level)

    def heat_output(self, results_dict):
        """
        Total energy
        """
        return results_dict[self.heat_budget_flow]['sequences']['flow']
