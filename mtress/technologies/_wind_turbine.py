# -*- coding: utf-8 -*-

"""
wind turbine wrapper for generic RenewableElectricitySource

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

from ._renewable_electricity_source import RenewableElectricitySource


class WindTurbine(RenewableElectricitySource):
    """
    wind turbine wrapper for generic RenewableElectricitySource
    """

    def __init__(
        self,
        nominal_power,
        specific_generation,
        funding,
        out_bus_internal,
        out_bus_external,
        label,
        energy_system,
    ):
        super().__init__(
            nominal_power,
            specific_generation,
            funding,
            out_bus_internal,
            out_bus_external,
            label,
            energy_system,
        )
