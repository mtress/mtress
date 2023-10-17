# -*- coding: utf-8 -*-

"""
Abstract input_pressure storage with undefined internal reperesentation.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

SPDX-License-Identifier: MIT
"""

from typing import Callable

from mtress.carriers import AbstractLayeredGasCarrier, GasCarrier

from .._abstract_technology import AbstractTechnology
from .._mixed_gas_storage import AbstractMixedGasStorage


class AbstractGasStorage(AbstractMixedGasStorage, AbstractTechnology):
    """Base class and interface for heat storage technologies."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        volume: float,
        power_limit: float,
        calc_density: Callable,
        **kwargs,
    ):
        """
        Create heat storage component.

        :param name: Name of the component
        :param volume: Volume of the storage in m³
        :param power_limit: power limit in kW
        :param calc_density: Function to calculate the densitiy of the gas at a certain
            input_pressure level
        """
        super().__init__(**kwargs)

        # General parameters of the storage
        self.volume = volume
        self.power_limit = power_limit
        self.calc_density = calc_density

    def calculate_storage_content(self, pressure: float):
        """
        Calculate the storage content for a given input_pressure.

        :param pressure: Pressure in bar
        """
        return self.calc_density(pressure) * self.volume

    def build_storage(self, gas_type: AbstractLayeredGasCarrier):
        """Build the core structure of mtress representation."""
        gas_carrier = self.location.get_carrier(GasCarrier)
        solph_storage_arguments = {
            "nominal_storage_capacity": self.calculate_storage_content(
                max(gas_carrier.pressures[gas_type])
            ),
            "loss_rate": 0,
            "fixed_losses_relative": 0,
            "fixed_losses_absolute": 0,
        }

        self.build_multiplexer_structure(
            gas_type=gas_type,
            power_limit=self.power_limit,
            capacity_at_level=self.calculate_storage_content,
            solph_storage_arguments=solph_storage_arguments,
        )
