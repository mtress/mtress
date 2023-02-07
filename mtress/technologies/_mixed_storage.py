# -*- coding: utf-8 -*-

"""
A fully mixed storage.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Sunke Schlüters

SPDX-License-Identifier: MIT
"""
import logging

from oemof.solph import Bus, Flow
from oemof.solph.components import GenericStorage
from oemof.thermal import stratified_thermal_storage

from .._abstract_component import AbstractSolphComponent
from .._data_handler import TimeseriesSpecifier
from .._oemof_storage_multiplexer import storage_multiplexer_constraint
from ..carriers import AbstractLayeredCarrier, Heat, Hydrogen
from ..physics import H2O_DENSITY, H2O_HEAT_CAPACITY, kJ_to_MWh
from ._abstract_technology import AbstractTechnology

# Thermal conductivity of insulation material
TC_INSULATION = 0.04  # W / (m * K)

_LOGGER = logging.getLogger(__name__)


class AbstractMixedStorage(AbstractTechnology, AbstractSolphComponent):
    """Abstract mixed storage."""

    def __init__(
        self,
        name: str,
        carrier: AbstractLayeredCarrier,
        capacity_per_unit: float,
        empty_level: float = 0,
        solph_storage_arguments: dict = None,
    ):
        """Initialize abstract mixed storage."""
        super().__init__(name)

        self.carrier = carrier
        self.capacity_per_unit = capacity_per_unit
        self.empty_level = empty_level

        if solph_storage_arguments is None:
            _LOGGER.warning(
                "No arguments for the underlying GenericStorage provided. Using defaults."
            )
            solph_storage_arguments = {
                "nominal_storage_capacity": (max(self.carrier.levels) - empty_level)
                * capacity_per_unit,
                "initial_storage_level": 0,
            }

        self.solph_storage_arguments = solph_storage_arguments

        self.storage_multiplexer_interfaces = {}
        self.multiplexer: Bus = None
        self.storage: GenericStorage = None

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
        # self._storage = self._solph_model.add_solph_component()
