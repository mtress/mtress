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
from .._energy_types import QualityStatus
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
        return (
            (bus1.energy_quality.minimum <= bus2.energy_quality.maximum).any()
            and (
                bus2.energy_quality.minimum <= bus1.energy_quality.maximum
            ).any()
        )

    def _nodes_with_overlap(self, node_list, bus):
        matching_nodes = []

        for node in node_list:
            if (
                node.parent is not bus.parent
                and HeatCarrier._have_overlap(node, bus)
            ):
                matching_nodes.append(node)

        matching_nodes.sort(
            key=lambda node: (node.temperature.min(), node.parent != self)
        )
        return matching_nodes

    def get_input_node(self, bus: TemperatureBus) -> TemperatureBus:
        candidate_nodes = list(
            self.parent.child_outbound_interfaces(EnergyType.HEAT)
        )
        matching_nodes = self._nodes_with_overlap(candidate_nodes, bus)
        return self._copy_if_needed(matching_nodes[0], bus)

    def get_output_node(self, bus: TemperatureBus) -> TemperatureBus:
        candidate_nodes = list(
            self.parent.child_inbound_interfaces(EnergyType.HEAT)
        )
        matching_nodes = self._nodes_with_overlap(candidate_nodes, bus)
        return self._copy_if_needed(matching_nodes[0], bus)

    def _copy_if_needed(self, bus1, bus_to_connect):
        if bus1.parent is self:
            return bus1
        else:
            minimum_temperature = np.maximum(
                bus1.energy_quality.minimum.to_numpy(),
                bus_to_connect.energy_quality.minimum.to_numpy(),
            )
            return self.add_level(minimum_temperature, fixed=True)

    def establish_interconnections(self):
        pass

    def add_level(self, t, *, fixed):
        if fixed:
            label = f"{t}"
        else:
            label = f"tn_{len(self.subnodes)}"
        node = self.subnode(
            TemperatureBus,
            local_name=label,
            temperature=EnergyQuality(t, fixed=fixed),
            quality_status=QualityStatus.INFERRED,
        )
        self.inbound_interfaces[EnergyType.HEAT] = self.subnodes
        self.outbound_interfaces[EnergyType.HEAT] = self.subnodes

        return node
