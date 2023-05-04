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

    SINGLE_FLOW: Allow only one flow to be active in each time step.
    MULTIPLE_FLOWS: Allow multiple flows to be active in each time step.
    """

    SINGLE_FLOW = "single_flow"
    MULTIPLE_FLOWS = "multiple_flows"


class AbstractMixedStorage(AbstractSolphComponent):
    """Abstract mixed storage."""

    def __init__(self, *, implementation: Implementation, **kwargs) -> None:
        """Initialize mixed storage."""
        super().__init__(**kwargs)

        self.implementation = implementation

        self.multiplexer: Optional[Bus] = None
        self.storage: Optional[GenericStorage] = None
        self.storage_multiplexer_interfaces: dict = {}
        self.storage_multiplexer_inputs: dict[float, Bus] = {}
        self.storage_multiplexer_outputs: dict[float, Bus] = {}

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
            (level - empty_level) * capacity_per_unit: carrier.outputs[level]
            for level in carrier.levels
        }
        self.storage_multiplexer_outputs = {
            (level - empty_level) * capacity_per_unit: carrier.inputs[level]
            for level in carrier.levels
        }
        self.storage_multiplexer_interfaces = {
            (level - empty_level)
            * capacity_per_unit: (
                carrier.inputs[level],
                carrier.outputs[level],
            )
            for level in carrier.levels
        }

        self.multiplexer = self.create_solph_component(
            label="multiplexer",
            component=Bus,
            inputs={
                bus: Flow(nominal_value=power_limit) for bus in carrier.inputs.values()
            },
            outputs={
                bus: Flow(nominal_value=power_limit) for bus in carrier.outputs.values()
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
        if self.implementation == Implementation.MULTIPLE_FLOWS:
            storage_multiplexer_constraint(
                model=self._solph_model.model,
                name=self.create_label("level_constraint"),
                storage_component=self.storage,
                multiplexer_component=self.multiplexer,
                interfaces=self.storage_multiplexer_interfaces,
            )

            return

        if self.implementation == Implementation.SINGLE_FLOW:
            storage_level_constraint(
                model=self._solph_model.model,
                name=self.create_label("level_constraint"),
                storage_component=self.storage,
                multiplexer_bus=self.multiplexer,
                inputs=self.storage_multiplexer_inputs,
                outputs=self.storage_multiplexer_outputs,
            )

            return

        raise NotImplementedError(
            f"Storage constraint implementation {self.implementation} not implement"
        )
