# -*- coding: utf-8 -*-

"""
Basic heat layer functionality.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""

from oemof.solph import Bus

from .._energy_types import EnergyType
from ._layered_carrier import AbstractLayeredCarrier


class HeatCarrier(AbstractLayeredCarrier):
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
        temperature_levels: list[int] = None,
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

        # Properties for solph interfaces
        self.level_nodes = {}

        self._build_core(temperature_levels)

    def _build_core(self, temperature_levels):
        """Build core structure of oemof.solph representation."""

        for temperature in temperature_levels:
            self.add_level(temperature)

        self.inbound_interfaces[EnergyType.HEAT] = self.subnodes
        self.outbound_interfaces[EnergyType.HEAT] = self.subnodes

    def establish_interconnections(self):
        # collect temparature levels
        interfaces = set(self.parent.get_interfaces(EnergyType.HEAT))

        # prevent duplicates from own node
        interfaces -= set(self.subnodes)

        temps = [
            t
            for i in interfaces
            if (t := i.custom_properties.get("temperature")) is not None
            and "preliminary" not in i.custom_properties
        ]

        # add nodes and update levels
        for t in temps:
            self.add_level(t)

    def add_level(self, t):
        self._levels.append(t)
        t_bus = self.subnode(
            Bus,
            local_name=f"T_{t}",
            custom_properties={"temperature": t},
        )
        self.level_nodes[t] = t_bus
