# -*- coding: utf-8 -*-

"""
A fully mixed storage.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Sunke Schlüters

SPDX-License-Identifier: MIT
"""

from enum import Enum
from typing import Callable, Optional

from oemof.solph import Bus, Flow
from oemof.solph.components import GenericStorage
from oemof.solph.constraints import storage_level_constraint

from .._abstract_component import AbstractSolphRepresentation
from .._oemof_storage_multiplexer import storage_multiplexer_constraint
from ..carriers import AbstractLayeredCarrier


class Implementation(Enum):
    """
    Possible multiplexer implementations.

    STRICT: Allow flows to be active only if storage content permits until the end of the time step.
    FLEXIBLE: Allow flows to be active if storage content permits at any time.
    """

    STRICT = "strict"
    FLEXIBLE = "flexible"


class AbstractHomogenousStorage(AbstractSolphRepresentation):
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
        levels: list,
        inputs: list[Bus],
        outputs: list[Bus],
        power_limit: float,
        capacity_at_level: Optional[Callable] = None,
        capacity_per_unit: Optional[float] = None,
        empty_level: float = 0,
        solph_storage_arguments: dict = None,
    ):
        """
        Build core solph structure.

        :param carrier: Carrier to connect to.
        :param power_limit: Power limit of the storage.
        :param capacity_at_level: Function to calculate the storage content for a given
            level, e.g. energy content at a given pressure level. If no function is
            given, linear relation between carrier quality and storage level is assumed.
        :param empty_level: Level which corresponds to an empty storage, e.g. the
            reference temperature of the heat carrier. This argument is only used in
            conjunction with capacity_per_unit.
        :param solph_storage_arguments: Additional arguments to be passed to the
            storage constructor, e.g. loss rates
        """

        self.storage_multiplexer_inputs = {}
        self.storage_multiplexer_outputs = {}

        max_level = max(levels)

        for level in levels:
            if capacity_at_level is not None:
                # Use user defined function calculating the storage content at level
                storage_level = capacity_at_level(level) / capacity_at_level(max_level)
            else:
                storage_level = (level - empty_level) / (max_level - empty_level)

            if storage_level > 0:
                in_bus = self.create_solph_node(
                    label=f"in_{level:d}",
                    node_type=Bus,
                    inputs={outputs[level]: Flow()},
                )
                self.storage_multiplexer_inputs[in_bus] = storage_level

            if storage_level < 1:
                out_bus = self.create_solph_node(
                    label=f"out_{level:d}",
                    node_type=Bus,
                    outputs={inputs[level]: Flow()},
                )

                self.storage_multiplexer_outputs[out_bus] = storage_level

        self.multiplexer = self.create_solph_node(
            label="multiplexer",
            node_type=Bus,
            inputs={
                bus: Flow(nominal_value=power_limit)
                for bus in self.storage_multiplexer_inputs
            },
            outputs={
                bus: Flow(nominal_value=power_limit)
                for bus in self.storage_multiplexer_outputs
            },
        )

        if solph_storage_arguments is None:
            solph_storage_arguments = {}

        self.storage = self.create_solph_node(
            label="storage",
            node_type=GenericStorage,
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
