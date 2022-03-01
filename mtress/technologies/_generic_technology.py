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
    IMPORT = auto()
    RENEWABLE = auto()


class GenericTechnology:
    """
    The class GenericTechnology is meant to be used as an interface
    """

    def __init__(self, label, energy_system):
        self._flows = {flow_type: set() for flow_type in FlowType}
        self._label = label
        self._energy_system = energy_system

    def categorise_flow(self, flow, flow_types):
        """
        categorises given flow under the named flow_types
        """
        for flow_type in flow_types | {FlowType.ALL}:
            if flow_type in self._flows:
                self._flows[flow_type].add(flow)
            else:
                self._flows[flow_type] = {flow}

    def get_flows(self, flow_types):
        """
        returns flows categorised under all named flow_types
        """
        flows = self._flows[FlowType.ALL].copy()
        for flow_type in flow_types:
            try:
                flows.intersection_update(self._flows[flow_type])
            except KeyError:
                return set()
        return flows
