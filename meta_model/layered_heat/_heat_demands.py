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


class HeatDemands:
    def __init__(self,
                 heat_layers,
                 heat_demands,
                 label,
                 forward_flow_temperature,
                 backward_flow_temperature):
        """
        :param heat_layers:
        :param heat_demands:
        :param label:
        :param forward_flow_temperature:
        :param backward_flow_temperature:
        """
        energy_system = heat_layers.energy_system

        self.thermal_sink_bus = solph.Bus(label=label + "_sink_bus")

        thermal_sink = solph.Sink(label=label+"_sink",
                                  inputs={self.thermal_sink_bus: solph.Flow()})

        heat_drop_ratio = ((celsius_to_kelvin(backward_flow_temperature)
                            - heat_layers.REFERENCE_TEMPERATURE)
                           / (celsius_to_kelvin(forward_flow_temperature)
                              - heat_layers.REFERENCE_TEMPERATURE))
        self.heat_drop_ratio = heat_drop_ratio
        heat_drop = solph.Transformer(
            label=label+"_drop",
            inputs={heat_layers.b_th[forward_flow_temperature]: solph.Flow()},
            outputs={heat_layers.b_th[backward_flow_temperature]: solph.Flow(),
                     self.thermal_sink_bus: solph.Flow(nominal_value=1,
                                                       fix=heat_demands)},
            conversion_factors={
                heat_layers.b_th[forward_flow_temperature]: 1,
                heat_layers.b_th[backward_flow_temperature]: heat_drop_ratio,
                self.thermal_sink_bus: 1 - heat_drop_ratio})

        energy_system.add(thermal_sink, self.thermal_sink_bus, heat_drop)
