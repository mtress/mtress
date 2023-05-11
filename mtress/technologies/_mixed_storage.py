# -*- coding: utf-8 -*-

"""
A fully mixed storage.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Sunke Schlüters

SPDX-License-Identifier: MIT
"""

from enum import Enum
from typing import Optional

from oemof.solph import Bus, Flow

from oemof.solph.components import GenericStorage

from .._abstract_component import AbstractSolphComponent
from .._oemof_storage_multiplexer import storage_multiplexer_constraint
from .._storage_level_constraint import storage_level_constraint
from ..carriers import AbstractLayeredCarrier


class Implementation(Enum):
    """
    Possible multiplexer implementations.

    STRICT: Allow flows to be active only if storage content permits until the end of the time step.
    FLEXIBLE: Allow flows to be active if storage content permits at any time.
    """

    STRICT = "strict"
    FLEXIBLE = "flexible"


class AbstractMixedStorage(AbstractSolphComponent):
    """Abstract mixed storage."""

    def __init__(self, *, implementation: Implementation, **kwargs) -> None:
        """Initialize mixed storage."""
        super().__init__(**kwargs)

        self.implementation = implementation

        self.multiplexer: Optional[Bus] = None
        self.storage: Optional[GenericStorage] = None
        self.storage_multiplexer_inputs: dict[Bus, float] = {}
        self.storage_multiplexer_outputs: dict[Bus, float] = {}

    def build_multiplexer_structure(  # pylint: disable=too-many-arguments
        self,
        carrier: AbstractLayeredCarrier,
        capacity_per_unit: float,
        power_limit: float,
        empty_level: float = 0,
        solph_storage_arguments: dict = None,
    ):
        """
        Build core solph structure.

        :param carrier: Carrier to connect to.
        :param capacity_per_unit: Storage capacity corresponding to one unit of the
            carrier, e.g. energy needed to heat the storage by 1K.
        :param empty_level: Level which corresponds to an empty storage, e.g. the
            reference temperature of the heat carrier
        :param solph_storage_arguments: Additional arguments to be passed to the
            storage constructor, e.g. loss rates
        """
        self.storage_multiplexer_inputs = {
            carrier.outputs[level]: (level - empty_level) * capacity_per_unit
            for level in carrier.levels
        }
        self.storage_multiplexer_outputs = {
            carrier.inputs[level]: (level - empty_level) * capacity_per_unit
            for level in carrier.levels
        }

        self.multiplexer = self.create_solph_component(
            label="multiplexer",
            component=Bus,
            inputs={
                bus: Flow(nominal_value=power_limit) for bus in carrier.outputs.values()
            },
            outputs={
                bus: Flow(nominal_value=power_limit) for bus in carrier.inputs.values()
            },
        )

        if solph_storage_arguments is None:
            solph_storage_arguments = {}

        self.storage = self.create_solph_component(
            label="storage",
            component=GenericStorage,
            inputs={self.multiplexer: Flow()},
            outputs={self.multiplexer: Flow()},
            **solph_storage_arguments,
        )

    def add_constraints(self):
        """Add constraints."""
        contraint_args = {
            "model": self._solph_model.model,
            "name": self.create_label("level_constraint"),
            "storage_component": self.storage,
            "multiplexer_bus": self.multiplexer,
            "input_levels": self.storage_multiplexer_inputs,
            "output_levels": self.storage_multiplexer_outputs,
        }

        if self.implementation == Implementation.FLEXIBLE:
            storage_multiplexer_constraint(**contraint_args)

            return

        if self.implementation == Implementation.STRICT:
            storage_level_constraint(**contraint_args)

            return

        raise NotImplementedError(
            f"Storage constraint implementation {self.implementation} not implement"
        )