# -*- coding: utf-8 -*-

"""
generic technology meta class

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

from enum import Enum, auto


class FlowType(Enum):
    ALL = auto()
    IN = auto()
    OUT = auto()
    PRODUCTION = auto()
    STORAGE = auto()
    EXPORT = auto()


class GenericTechnology:
    """
    The class GenericTechnology is meant to be used as an interface
    """
    def __init__(self,
                 label):
        self._flows = {flow_type: set() for flow_type in FlowType}
        self._label = label
        self._solph_nodes = set()

    def _categorise_flow(self, flow, flow_types):
        """
        categorises given flow under the named flow_types
        """
        for flow_type in flow_types | {FlowType.ALL}:
            self._flows[flow_type].add(flow)

    def get_flows(self, flow_types):
        """
        returns flows categorised under all named flow_types
        """
        flows = self._flows[FlowType.ALL].copy()
        for flow_type in flow_types:
            flows.intersection_update(self._flows[flow_type])
        return flows

    @property
    def solph_nodes(self):
        """
        getter to add solph nodes to energy system

        (alternative would be to hand a reference to the energy system
        to the init function)
        """
        return self._solph_nodes
