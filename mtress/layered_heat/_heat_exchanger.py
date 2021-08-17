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


class HeatExchanger:
    """
    For modeling power demands that lower temperature,
    see https://arxiv.org/abs/2012.12664

    HeatLayers  HeatExchanger       Demand

       (Q(T3))
              ↘
             [HE3,2]----------------->(D(T3))
              ↙
       (Q(T2))
    """
    def __init__(self,
                 heat_layers,
                 heat_demand,
                 label,
                 forward_flow_temperature,
                 backward_flow_temperature=None):
        """
        :param heat_layers: HeatLayers object to attach to
        :param heat_demand: solph.Node (e.g. solph.Bus)
        :param label: name for HeatExchanger
        :param forward_flow_temperature: flow temperature
        :param backward_flow_temperature: return temperature
        """
        energy_system = heat_layers.energy_system

        if heat_layers.reference_temperature < backward_flow_temperature:
            heat_drop_ratio = ((backward_flow_temperature
                                - heat_layers.reference_temperature)
                               / (forward_flow_temperature
                                  - heat_layers.reference_temperature))
            self.heat_drop_ratio = heat_drop_ratio

            heat_drop = solph.Transformer(
                label=label,
                inputs={
                    heat_layers.b_th[forward_flow_temperature]: solph.Flow()},
                outputs={
                    heat_layers.b_th[backward_flow_temperature]: solph.Flow(),
                    heat_demand: solph.Flow()},
                conversion_factors={
                    heat_layers.b_th[forward_flow_temperature]: 1,
                    heat_layers.b_th[backward_flow_temperature]:
                        heat_drop_ratio,
                    heat_demand: 1 - heat_drop_ratio})

            self.backward_flow = (
                heat_drop.label,
                heat_layers.b_th[backward_flow_temperature].label)
        else:
            self.heat_drop_ratio = 0
            heat_drop = solph.Bus(
                label=label,
                inputs={
                    heat_layers.b_th[forward_flow_temperature]: solph.Flow()},
                outputs={heat_demand: solph.Flow()})

        self.forward_flow = (heat_layers.b_th[forward_flow_temperature].label,
                             heat_drop.label)

        self.supply_flow = (heat_drop.label, heat_demand)

        energy_system.add(heat_drop)

    def heat_output(self, results_dict):
        """
        :param results_dict: dictionary containing result sequences

        Total energy calculated as
        difference between forward and backward flows
        """
        return results_dict[self.supply_flow]['sequences']['flow']
