# -*- coding: utf-8 -*-

"""
Abstract gas pressure storage with undefined internal representation.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

SPDX-License-Identifier: MIT
"""

from typing import Callable

from mtress.carriers import GasCarrier

from ...physics import Gas
from .._abstract_homogenous_storage import (
    AbstractHomogenousStorage,
    Implementation,
)
from .._abstract_technology import AbstractTechnology


class GasStorage(AbstractHomogenousStorage, AbstractTechnology):
    """Base class and interface for gas storage technologies."""

    def __init__(
        self,
        name,
        gas_type: Gas,
        volume: float,
        power_limit: float,
        calc_density: Callable,
        implementation: Implementation | str = Implementation.STRICT,
    ):
        """
        Create gas pressure storage component.

        :param name: Name of the component
        :param gas_type: Type of gas (HYDROGEN, NATURAL GAS, BIO-METHANE
                         BIOGAS, etc.)
        :param volume: Volume of the storage in m³
        :param power_limit: power limit in kg
        :param calc_density: Function to calculate the density of the gas
                             at a certain pressure level

        """
        if not isinstance(implementation, Implementation):
            implementation = Implementation(implementation)
        super().__init__(name=name, implementation=implementation)

        # General parameters of the storage
        self.gas_type = gas_type
        self.volume = volume
        self.power_limit = power_limit
        self.calc_density = calc_density

    def _storage_content(self, pressure: float):
        """
        Calculate the storage content at a given pressure.

        :param pressure: Pressure inside the storage tank given in bar
        """
        return self.calc_density(pressure) * self.volume

    def build_core(self) -> None:
        """Build the core structure of mtress representation."""
        gas_carrier = self.location.get_carrier(GasCarrier)
        solph_storage_arguments = {
            "nominal_storage_capacity": self._storage_content(
                max(gas_carrier.pressure_levels[self.gas_type])
            ),
            "loss_rate": 0,
            "fixed_losses_relative": 0,
            "fixed_losses_absolute": 0,
        }

        self.build_multiplexer_structure(
            levels=gas_carrier.pressure_levels[self.gas_type],
            inputs=gas_carrier.inputs[self.gas_type],
            outputs=gas_carrier.outputs[self.gas_type],
            power_limit=self.power_limit,
            capacity_at_level=self._storage_content,
            solph_storage_arguments=solph_storage_arguments,
        )
