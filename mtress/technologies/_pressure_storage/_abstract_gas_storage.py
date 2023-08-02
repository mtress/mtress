# -*- coding: utf-8 -*-

"""
Abstract pressure storage with undefined internal reperesentation.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

SPDX-License-Identifier: MIT
"""

from typing import Callable

from mtress.carriers import AbstractLayeredCarrier

from .._abstract_technology import AbstractTechnology
from .._mixed_storage import AbstractMixedStorage


class AbstractGasStorage(AbstractMixedStorage, AbstractTechnology):
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
            pressure level
        """
        super().__init__(**kwargs)

        # General parameters of the storage
        self.volume = volume
        self.power_limit = power_limit
        self.calc_density = calc_density

    def calculate_storage_content(self, pressure: float):
        """
        Calculate the storage content for a given pressure.

        :param pressure: Pressure in bar
        """
        return self.calc_density(pressure) * self.volume

    def build_storage(self, carrier: AbstractLayeredCarrier):
        """Build the core structure of mtress representation."""
        empty_level = 0

        solph_storage_arguments = {
            "nominal_storage_capacity": self.calculate_storage_content(
                max(carrier.levels)
            ),
            "loss_rate": 0,
            "fixed_losses_relative": 0,
            "fixed_losses_absolute": 0,
        }

        self.build_multiplexer_structure(
            carrier,
            self.calculate_storage_content,
            self.power_limit,
            empty_level,
            solph_storage_arguments,
        )
