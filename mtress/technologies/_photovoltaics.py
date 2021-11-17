# -*- coding: utf-8 -*-

"""
basic heat layer functionality

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

from oemof.solph import Bus
from oemof.solph import Flow
from oemof.solph import Source

from ._generic_technology import GenericTechnology


class Photovoltaics(GenericTechnology):
    def __init__(self,
                 nominal_power,
                 specific_generation,
                 funding,
                 out_bus_internal,
                 out_bus_external,
                 label):
        super().__init__(label)

        b_el_pv = Bus(
            label="b_el_pv",
            outputs={
                out_bus_external: Flow(variable_costs=-funding),
                out_bus_internal: Flow()})
        t_pv = Source(
            label='t_pv',
            outputs={
                b_el_pv: Flow(nominal_value=nominal_power,
                              max=specific_generation)})

        self._flows_in["solar"] = (t_pv.label, b_el_pv.label)
        self._flows_out["export"] = (b_el_pv.label, out_bus_external.label)

        self._solph_nodes.add(t_pv)
        self._solph_nodes.add(b_el_pv)
