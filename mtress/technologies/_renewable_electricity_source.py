# -*- coding: utf-8 -*-

"""
basic heat layer functionality

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

from oemof.solph import Bus
from oemof.solph import Flow
from oemof.solph import Source

from ._generic_technology import (
    FlowType,
    GenericTechnology,
)


class RenewableElectricitySource(GenericTechnology):
    """
    a generic electricity source
    """

    def __init__(
        self,
        nominal_power,
        specific_generation,
        funding,
        out_bus_internal,
        out_bus_external,
        label,
        energy_system,
    ):
        super().__init__(label, energy_system)

        bus = Bus(
            label=self._label + "_bus",
            outputs={
                out_bus_external: Flow(variable_costs=-funding),
                out_bus_internal: Flow(),
            },
        )
        source = Source(
            label=self._label + "_source",
            outputs={bus: Flow(nominal_value=nominal_power, max=specific_generation)},
        )

        self.categorise_flow(
            (source.label, bus.label),
            {FlowType.OUT, FlowType.PRODUCTION, FlowType.RENEWABLE},
        )
        self.categorise_flow(
            (bus.label, out_bus_external.label),
            {FlowType.OUT, FlowType.EXPORT, FlowType.RENEWABLE},
        )

        self._energy_system.add(source)
        self._energy_system.add(bus)
