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

from ._abstract_carrier import AbstractLayeredCarrier


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
        temperature_levels: list[float],
        specific_heat_capacity=1.161,
    ):
        """
        Initialize heat energy carrier and add components.

        :param temperature_levels: list of temperatures (in °C)
        :param specific_heat_capacity: heat capacity (in Wh/kg/K)
        """
        super().__init__(
            levels=sorted(temperature_levels),
        )
        self.specific_heat_capacity = specific_heat_capacity

        # Properties for solph interfaces
        self.level_nodes = {}

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        for temperature in self._levels:
            self.level_nodes[temperature] = self.create_solph_node(
                label=f"T_{temperature:.0f}",
                node_type=Bus,
                custom_properties={"temperature": temperature},
            )
