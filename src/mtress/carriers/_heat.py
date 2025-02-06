# -*- coding: utf-8 -*-

"""
Basic heat layer functionality.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""
from oemof.solph import Bus, Flow, components

from .._abstract_component import AbstractSolphRepresentation
from ._abstract_carrier import AbstractLayeredCarrier


class HeatCarrier(AbstractLayeredCarrier, AbstractSolphRepresentation):
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

        Notice that the assumption of a hydraulic system typically does not
        impact the result. It is just to have a temperate-independent measure
        for the energy, meaning that the sum of flows into and out of the
        HeatCarrier and all attached Technologies should be zero although
        the latter increase or dectrease the energy.

        Other components and demands might be added to the energy_system by
        their respective classes / functions and are automatically connected
        to their fitting busses by the carrier.
    """

    def __init__(
        self,
        temperature_levels: list[float],
        specific_heat_capacity = 1.161,
        missing_heat_penalty: float = 1e9,
        excess_heat_penalty: float = 1e9,
    ):
        """
        Initialize heat energy carrier and add components.

        :param temperature_levels: list of temperatures (in °C)
        :param specific_heat_capacity: heat capacity (in Wh/kg/K)
        :param missing_heat_penalty: assigns a cost for each unit of missing
            heat produced (in any currency)
        :param excess_heat_penalty: assigns a cost for each unit of excess
            heat produced (in any currency)
        """
        super().__init__(
            levels=sorted(temperature_levels),
        )
        self.specific_heat_capacity = specific_heat_capacity
        self.missing_heat_penalty = missing_heat_penalty
        self.excess_heat_penalty = excess_heat_penalty

        # Properties for solph interfaces
        self.level_nodes = {}

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        for temperature in self._levels:
            self.level_nodes[temperature] = self.create_solph_node(
                label=f"T_{temperature:.0f}",
                node_type=Bus,
            )

        self.create_solph_node(
            label="excess_heat",
            node_type=components.Sink,
            inputs={
                bus: Flow(variable_costs=self.excess_heat_penalty)
                for bus in self.level_nodes.values()
            },
        )

        self.create_solph_node(
            label="missing_heat",
            node_type=components.Source,
            outputs={
                bus: Flow(variable_costs=self.missing_heat_penalty)
                for bus in self.level_nodes.values()
            },
        )

    def establish_interconnections(self) -> None:
        pass

    def get_connection_heat_transfer(self, max_temp, min_temp):
        warm_level_heating, _ = self.get_surrounding_levels(max_temp)
        _, cold_level_heating = self.get_surrounding_levels(min_temp)

        if cold_level_heating not in self.levels:
            raise ValueError(
                f"""No suitable temperature level available 
                for {cold_level_heating}."""
            )
        if warm_level_heating not in self.levels:
            raise ValueError(
                f"""No suitable temperature level available 
                for {warm_level_heating}."""
            )

        ratio = (cold_level_heating - self.reference) / (
            warm_level_heating - self.reference
        )

        heat_bus_warm = self.level_nodes[warm_level_heating]
        heat_bus_cold = self.level_nodes[cold_level_heating]

        return heat_bus_warm, heat_bus_cold, ratio
