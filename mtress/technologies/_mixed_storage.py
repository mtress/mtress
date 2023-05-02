# -*- coding: utf-8 -*-

"""
A fully mixed storage.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Sunke Schlüters

SPDX-License-Identifier: MIT
"""

from enum import Enum

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

    multiplexer: Bus
    storage: GenericStorage
    storage_multiplexer_interfaces: dict = None

    def __init__(self, implementation: Implementation) -> None:
        """Initialize mixed storage."""
        self.implementation = implementation
        super().__init__()

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
        self.storage_multiplexer_interfaces = {
            (level - empty_level)
            * capacity_per_unit: (
                carrier.inputs[level],
                carrier.outputs[level],
            )
            for level in carrier.levels
        }

        self.multiplexer = self._solph_model.add_solph_component(
            mtress_component=self,
            label="multiplexer",
            solph_component=Bus,
            inputs={
                bus: Flow(nominal_value=power_limit) for bus in carrier.inputs.values()
            },
            outputs={
                bus: Flow(nominal_value=power_limit) for bus in carrier.outputs.values()
            },
        )

        if solph_storage_arguments is None:
            solph_storage_arguments = {}

        self.storage = self._solph_model.add_solph_component(
            mtress_component=self,
            label="storage",
            solph_component=GenericStorage,
            inputs={self.multiplexer: Flow()},
            outputs={self.multiplexer: Flow()},
            **solph_storage_arguments
        )

    def add_constraints(self):
        """Add constraints."""
        if self.implementation == Implementation.MULTIPLE_FLOWS:
            storage_multiplexer_constraint(
                model=self._solph_model.model,
                name=self._solph_model.get_label(self, "level_constraint"),
                storage_component=self.storage,
                multiplexer_component=self.multiplexer,
                interfaces=self.storage_multiplexer_interfaces,
            )

            return

        if self.implementation == Implementation.SINGLE_FLOW:
            input_levels = {}
            output_levels = {}

            for level, (
                input_component,
                output_component,
            ) in self.storage_multiplexer_interfaces.items():
                input_levels[input_component] = (
                    level / self.storage.nominal_storage_capacity
                )
                output_levels[output_component] = (
                    level / self.storage.nominal_storage_capacity
                )

            storage_level_constraint(
                model=self._solph_model.model,
                name=self._solph_model.get_label(self, "level_constraint"),
                storage_component=self.storage,
                multiplexer_bus=self.multiplexer,
                input_levels=input_levels,
                output_levels=output_levels,
            )

            return
