# -*- coding: utf-8 -*-

"""
Basic heat layer functionality.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""

from collections.abc import Iterable

import numpy as np

from .._base_mtress_nodes import AbstractCarrier
from .._energy_types import EnergyType
from .._energy_types import EnergyQuality
from .._energy_types import TemperatureBus


class HeatCarrier(AbstractCarrier):
    """
    Connector class for modelling power flows with variable temperature levels.

    This class models is a heat bus system with configurable temperature levels
    (original concept at https://arxiv.org/abs/2012.12664). The temperature
    levels can represent flow and return of a room heating system or various
    tapping temperatures.

    Functionality: Heat connections at a location. This class represents a
        local heat distribution system (assumed to be hydraulic).
        The energy carrier heat allows to optimise both, temperature and heat,
        as the temperature has a significant impact on the performance of
        renewable energy supply systems. This is done by defining several
        discrete temperature levels.

        Note that the assumption of a hydraulic system does not normally
        affect the result. It is simply a matter of having a temperature-
        independent measure of energy, meaning that the sum of the flows into
        and out of the HeatCarrier and all attached Technologies should be
        zero, even if the latter increase or decrease the energy.

        Other components and demands might be added to the energy_system by
        their respective classes / functions and are automatically connected
        to their fitting busses by the carrier.
    """

    def __init__(
        self,
        label,
        *,
        parent_node=None,
        custom_properties=None,
        temperature_levels=None,
        specific_heat_capacity=1.161,
    ):
        """
        Initialize heat energy carrier and add components.

        :param specific_heat_capacity: heat capacity (in Wh/kg/K)
        """
        super().__init__(
            label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )
        if temperature_levels is None:
            temperature_levels = []
        self.specific_heat_capacity = specific_heat_capacity

        self._build_core(temperature_levels)

    def _build_core(self, temperature_levels):
        """Build core structure of oemof.solph representation."""

        for temperature in temperature_levels:
            self.add_level(temperature, fixed=True)

    @property
    def temperatures(self) -> Iterable:
        for node in self._subnodes:
            node : TemperatureBus
            yield node.temperature

    @staticmethod
    def _have_overlap(bus1: TemperatureBus, bus2: TemperatureBus):
        b1_min = bus1.energy_quality.minimum
        b1_max = bus1.energy_quality.maximum
        b2_min = bus2.energy_quality.minimum
        b2_max = bus2.energy_quality.maximum

        if b1_min is None or b2_max is None:
            cond1 = True
        else:
            cond1 = (b1_min <= b2_max).any()
        if b2_min is None or b1_max is None:
            cond2 = True
        else:
            cond2 = (b2_min <= b1_max).any()

        return cond1 and cond2

    def nodes_to_connect(self, bus: TemperatureBus) -> list[TemperatureBus]:
        matching_nodes = []

        for node in self._subnodes:
            if (
                node.parent is not bus.parent
                and HeatCarrier._have_overlap(node, bus)
            ):
                matching_nodes.append(node)

        matching_nodes.sort(
            key=lambda node: (node.temperature.min())
        )
        return matching_nodes

    def establish_interconnections(self):
        pass
        # TODO: Iterate over known interfaces and create copies
        # for ...:
        #     self.add_level()

    def add_level(self, t, *, fixed):
        if fixed:
            label = f"{t}"
        else:
            label = f"tn_{len(self.subnodes)}"
        node = self.subnode(
            TemperatureBus,
            local_name=label,
            temperature=EnergyQuality(t, fixed=fixed),
        )
        self.inbound_interfaces[HeatCarrier] = self.subnodes
        self.outbound_interfaces[HeatCarrier] = self.subnodes

        return node
