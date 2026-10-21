# -*- coding: utf-8 -*-

"""
Gas carrier.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

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
from ._gas_bus import GasBus


class GasCarrier(AbstractCarrier):
    """
    GasCarrier is the container for different types of gases, which
    considers the gas properties from dataclass Gas. All gas flows,
    be it Hydrogen, Natural gas, Biogas or Bio-Methane, are considered
    to be in kg to maintain resiliency in the modelling.

    """

    def __init__(
        self,
        label,
        *,
        parent_node=None,
        custom_properties=None,
        pressure_levels=None,
    ):
        """
        Initialize gas energy carrier and add components.
        """
        super().__init__(
            label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )
        if pressure_levels is None:
            pressure_levels = []

        self._build_core(pressure_levels)

        if isinstance(self._parent, Location):
            self.establish_interconnections()

    def _build_core(self, pressure_levels):
        """Build core structure of oemof.solph representation."""

        for temperature in pressure_levels:
            self.get_level(temperature)

    @property
    def temperatures(self) -> Iterable:
        for node in self._subnodes:
            node: GasBus
            yield node.pressure

    @staticmethod
    def _have_overlap(bus1: GasBus, bus2: GasBus) -> bool:
        overlap = GasCarrier._overlap(bus1=bus1, bus2=bus2)
        return len(overlap) >= 1

    def _create_overlap_nodes(
            self,
            buses1: Iterable[GasBus],
            buses2: Iterable[GasBus],
        ):
        for bus1 in buses1:
            for bus2 in buses2:
                if (bus1.parent is not bus2.parent) or bus1.parent is None:
                    for temperature in GasCarrier._overlap(bus1, bus2):
                        self.get_level(temperature)

    @staticmethod
    def _overlap(bus1: GasBus, bus2: GasBus) -> tuple:
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

    def nodes_to_connect(self, bus: GasBus) -> deque[GasBus]:
        matching_nodes = []

        for node in self._subnodes:
            if GasCarrier._have_overlap(node, bus):
                matching_nodes.append(node)

        matching_nodes.sort(key=lambda node: node.pressure.min())
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
                if isinstance(x, GasBus)
            ]
            outbound_nodes += [
                x
                for x in tech.outbound_interfaces
                if isinstance(x, GasBus)
            ]

        self._create_overlap_nodes(inbound_nodes, outbound_nodes)

    def get_level(self, pressure) -> GasBus:
        quality = EnergyQuality(pressure)

        for node in self.subnodes:
            node: GasBus
            if quality == node.energy_quality:
                return node

        local_name = f"{pressure}"
        node = self.subnode(
            GasBus,
            local_name=local_name,
            temperature=quality,
        )
        self.inbound_interfaces.add(node)
        self.outbound_interfaces.add(node)

        return node
