# -*- coding: utf-8 -*-

"""
basic heat layer functionality

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

from oemof import solph

from ..carriers import Electricity

from ._abstract_technology import (
    AbstractTechnology,
)


class RenewableElectricitySource(AbstractTechnology):
    """
    a generic electricity source
    """

    def __init__(
        self,
        location,
        name,
        nominal_power,
        specific_generation,
    ):
        super().__init__(location=location, name=name)

        # Add electrical connection
        electricity_carrier = self.location.get_carrier(Electricity)

        self._electricity_bus = electricity_bus = solph.Bus(
            label=self._generate_label("electricity"),
            inputs={electricity_carrier.production: solph.Flow()},
        )

        self.location.energy_system.add(electricity_bus)
