# -*- coding: utf-8 -*-

"""
Basic heat layer functionality.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""

from collections import deque
from collections.abc import Iterable

import numpy as np

from oemof.solph import _plumbing

from mtress._location import Location

from .._plumbing import maxseq, minseq
from .._base_mtress_nodes import AbstractCarrier, AbstractTechnology
from .._energy_types import EnergyQuality, TemperatureBus


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
            node: TemperatureBus
            yield node.temperature

    @staticmethod
    def _have_overlap(bus1: TemperatureBus, bus2: TemperatureBus) -> bool:
        overlap = HeatCarrier._overlap(bus1=bus1, bus2=bus2)
        return len(overlap) >= 1

    @staticmethod
    def _overlap(bus1: TemperatureBus, bus2: TemperatureBus) -> tuple:
        b1_min = bus1.energy_quality.minimum
        b1_max = bus1.energy_quality.maximum
        b2_min = bus2.energy_quality.minimum
        b2_max = bus2.energy_quality.maximum

        lower_limit = maxseq(b1_min, b2_min)
        upper_limit = minseq(b1_max, b2_max)

        correct_order_mask = lower_limit < upper_limit

        if correct_order_mask.max() == 1:
            if not isinstance(correct_order_mask, _plumbing._FakeSequence):
                correct_order_mask = [
                    x if x else np.nan for x in correct_order_mask
                ]

            return (
                lower_limit * correct_order_mask,
                upper_limit * correct_order_mask,
            )

        both_same_mask = lower_limit == upper_limit
        if both_same_mask.max() == 1:
            if not isinstance(both_same_mask, _plumbing._FakeSequence):
                both_same_mask = [x if x else np.nan for x in both_same_mask]
            return (lower_limit * both_same_mask, )

        return tuple()

    def nodes_to_connect(self, bus: TemperatureBus) -> deque[TemperatureBus]:
        matching_nodes = []

        for node in self._subnodes:
            if HeatCarrier._have_overlap(node, bus):
                matching_nodes.append(node)

        matching_nodes.sort(key=lambda node: node.temperature.min())
        return deque(matching_nodes)

    def establish_interconnections(self):
        return

        self.parent: Location
        technologies = self.parent.get_nodes_by_type(AbstractTechnology)
        inbound_nodes = []
        outbound_nodes = []
        for tech in technologies:
            tech: AbstractTechnology
            inbound_nodes += [
                x
                for x in tech.inbound_interfaces
                if isinstance(x, TemperatureBus)
            ]
            outbound_nodes += [
                x
                for x in tech.outbound_interfaces
                if isinstance(x, TemperatureBus)
            ]

        # test
        t = set()
        for n in inbound_nodes + outbound_nodes:
            n: TemperatureBus
            t.add(n.temperature.value)

        for x in t:
            self.add_level(x, fixed=True)

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
        self.inbound_interfaces = self.subnodes
        self.outbound_interfaces = self.subnodes

        return node
