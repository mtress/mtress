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
            level, e.g. energy content at a given pressure level. Exactly one of
            capacity_at_level and capacity_per_unit must be given.
        :param capacity_per_unit: Storage capacity corresponding to one unit of the
            carrier, e.g. energy needed to heat the storage by 1K. Exactly one of
            capacity_at_level and capacity_per_unit must be given.
        :param empty_level: Level which corresponds to an empty storage, e.g. the
            reference temperature of the heat carrier. This argument is only used in
            conjunction with capacity_per_unit.
        :param solph_storage_arguments: Additional arguments to be passed to the
            storage constructor, e.g. loss rates
        """
        if (capacity_at_level is None) == (capacity_per_unit is None):
            raise ValueError(
                "Exactly one of capacity_at_level and capacity_per_unit must be given"
            )

        self.storage_multiplexer_inputs = {}
        self.storage_multiplexer_outputs = {}

        for level in carrier.levels:
            if capacity_per_unit is not None:
                storage_level = (level - empty_level) * capacity_per_unit
            else:
                # Use user defined function calculating the storage content at level
                storage_level = capacity_at_level(level)

            in_bus = self.create_solph_component(
                label=f"in_{level:d}",
                component=Bus,
                inputs={carrier.outputs[level]: Flow()},
            )

            self.storage_multiplexer_inputs[in_bus] = storage_level

            out_bus = self.create_solph_component(
                label=f"out_{level:d}",
                component=Bus,
                outputs={carrier.inputs[level]: Flow()},
            )

            self.storage_multiplexer_outputs[out_bus] = storage_level

        self.multiplexer = self.create_solph_component(
            label="multiplexer",
            component=Bus,
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
