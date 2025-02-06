# -*- coding: utf-8 -*-

"""
Basic heat layer functionality.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""
import numpy as np
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

    (T3) -> (T2) -> (T1) -> (T0)

    Functionality: Heat connections at a location. This class represents a
        local heat distribution system (typically hydraulic).
        The energy carrier heat allows to optimise both, temperature and heat,
        as the temperature has a significant impact on the performance of
        renewable energy supply systems. This is done by defining several
        discrete temperature levels.
        Besides the temperature levels, a reference temperature is defined,
        that is used to calculate the values of heat flows from, to an inside
        the carrier.

        Other components and demands might be added to the energy_system by
        their respective classes / functions and are automatically connected
        to their fitting busses by the carrier.
    """

    def __init__(
        self,
        temperature_levels: list[float],
        reference_temperature: float = 0,
    ):
        """
        Initialize heat energy carrier and add components.

        :param temperature_levels: list of temperatures (in °C)
        :param reference_temperature: Reference temperature (in °C)
        :param missing_heat_penalty: assigns a cost for each unit of missing
            heat produced (in any currency)
        :param excess_heat_penalty: assigns a cost for each unit of excess
            heat produced (in any currency)
        """
        if reference_temperature in temperature_levels:
            raise ValueError(
                "Reference temperature is not a valid temperature level."
            )
        super().__init__(
            levels=sorted(temperature_levels),
            reference=reference_temperature,
        )

        self._reference_index = np.searchsorted(
            self.levels, reference_temperature
        )

        # Properties for solph interfaces
        self.level_nodes = {}

    @property
    def reference_level(self):
        """Return index or key of reference level"""
        return self._reference_index

    @property
    def levels_above_reference(self):
        return self.levels[self._reference_index :]

    @property
    def levels_below_reference(self):
        return self.levels[: self._reference_index]

    @property
    def input_levels(self):
        """Return the list of input temperature levels."""
        return self.levels[1:]

    @property
    def output_levels(self):
        """Return the list of output temperature levels."""
        return self.levels

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        for temperature in self._levels:
            self.level_nodes[temperature] = self.create_solph_node(
                label=f"T_{temperature:.0f}",
                node_type=Bus,
            )

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
