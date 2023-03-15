# -*- coding: utf-8 -*-

"""
A fully mixed storage.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Sunke Schlüters

SPDX-License-Identifier: MIT
"""

from oemof.solph import Bus, Flow
from oemof.solph.components import GenericStorage

from .._abstract_component import AbstractSolphComponent
from .._oemof_storage_multiplexer import storage_multiplexer_constraint
from ..carriers import AbstractLayeredCarrier


class AbstractMixedStorage(AbstractSolphComponent):
    """Abstract mixed storage."""

    carrier: AbstractLayeredCarrier
    capacity_per_unit: float
    empty_level: float = 0
    solph_storage_arguments: dict = None

    multiplexer: Bus
    storage: GenericStorage
    storage_multiplexer_interfaces: dict = None

    def build_core(self):
        """Build core solph structure."""
        self.storage_multiplexer_interfaces = {
            (level - self.empty_level)
            * self.capacity_per_unit: (
                self.carrier.inputs[level],
                self.carrier.outputs[level],
            )
            for level in self.carrier.levels
        }

        self.multiplexer = self._solph_model.add_solph_component(
            mtress_component=self,
            label="multiplexer",
            solph_component=Bus,
            inputs={bus: Flow() for bus in self.carrier.inputs.values()},
            outputs={bus: Flow() for bus in self.carrier.outputs.values()},
        )

        self.storage = self._solph_model.add_solph_component(
            mtress_component=self,
            label="storage",
            solph_component=GenericStorage,
            inputs={self.multiplexer: Flow()},
            outputs={self.multiplexer: Flow()},
            **self.solph_storage_arguments
        )

    def add_constraints(self):
        """Add constraints."""
        storage_multiplexer_constraint(
            model=self._solph_model.model,
            name="some_name",
            storage_component=self.storage,
            multiplexer_component=self.multiplexer,
            interfaces=self.storage_multiplexer_interfaces,
        )
