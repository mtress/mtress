# -*- coding: utf-8 -*-

"""
Basic heat layer functionality.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

from collections import deque
from collections.abc import Iterable

import numpy as np

from oemof.solph._plumbing import _FakeSequence
from oemof.solph._plumbing import sequence

from mtress._location import Location

from ..._plumbing import maxseq, minseq
from ..._base_mtress_nodes import AbstractCarrier, AbstractTechnology
from ..._energy_quality import EnergyQuality
from ._heat_bus import TemperatureBus


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

        if isinstance(self._parent, Location):
            self.establish_interconnections()

    def _build_core(self, temperature_levels):
        """Build core structure of oemof.solph representation."""

        for temperature in temperature_levels:
            self.get_level(temperature)

    @property
    def temperatures(self) -> Iterable:
        for node in self._subnodes:
            node: TemperatureBus
            yield node.temperature

    @staticmethod
    def _have_overlap(bus1: TemperatureBus, bus2: TemperatureBus) -> bool:
        overlap = HeatCarrier._overlap(bus1=bus1, bus2=bus2)
        return len(overlap) >= 1

    def _create_overlap_nodes(
            self,
            buses1: Iterable[TemperatureBus],
            buses2: Iterable[TemperatureBus],
        ):
        for bus1 in buses1:
            for bus2 in buses2:
                if (bus1.parent is not bus2.parent) or bus1.parent is None:
                    for temperature in HeatCarrier._overlap(bus1, bus2):
                        self.get_level(temperature)

    @staticmethod
    def _overlap(bus1: TemperatureBus, bus2: TemperatureBus) -> tuple:
        """
        returns tuple[minimum_of_overlap, maximum_of_overlap, ]
        or returns tuple[both_same, ], or empty tuple
        """
        b1_min = bus1.energy_quality.minimum
        b1_max = bus1.energy_quality.maximum
        b2_min = bus2.energy_quality.minimum
        b2_max = bus2.energy_quality.maximum

        lower_limit = maxseq(b1_min, b2_min)
        upper_limit = minseq(b1_max, b2_max)

        correct_order_mask = lower_limit < upper_limit

        length = None
        if correct_order_mask.max() == 1:
            if not isinstance(correct_order_mask, _FakeSequence):
                length = len(correct_order_mask)
                correct_order_mask = [
                    x if x else np.nan for x in correct_order_mask
                ]

            return (
                correct_order_mask * sequence(lower_limit, length),
                correct_order_mask * sequence(upper_limit, length),
            )

        both_same_mask = lower_limit == upper_limit
        if both_same_mask.max() == 1:
            if not isinstance(both_same_mask, _FakeSequence):
                length = len(correct_order_mask)
                both_same_mask = [x if x else np.nan for x in both_same_mask]
            return (both_same_mask * sequence(lower_limit, length), )

        return tuple()

    def nodes_to_connect(self, bus: TemperatureBus) -> deque[TemperatureBus]:
        matching_nodes = []

        for node in self._subnodes:
            if HeatCarrier._have_overlap(node, bus):
                matching_nodes.append(node)

        matching_nodes.sort(key=lambda node: node.temperature.min())
        return deque(matching_nodes)

    def establish_interconnections(self):

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

        self._create_overlap_nodes(inbound_nodes, outbound_nodes)

    def get_level(self, temperature) -> TemperatureBus:
        quality = EnergyQuality(temperature)

        for node in self.subnodes:
            node: TemperatureBus
            if quality == node.energy_quality:
                return node

        local_name = f"{temperature}"
        node = self.subnode(
            TemperatureBus,
            local_name=local_name,
            temperature=quality,
        )
        self.inbound_interfaces.add(node)
        self.outbound_interfaces.add(node)

        return node
