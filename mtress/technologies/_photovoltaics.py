# -*- coding: utf-8 -*-

"""
pv wrapper for generic RenewableElectricitySource

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

from ._renewable_electricity_source import RenewableElectricitySource


class Photovoltaics(RenewableElectricitySource):
    """
    photovoltaics wrapper for generic RenewableElectricitySource
    """
    def __init__(self,
                 nominal_power,
                 specific_generation,
                 funding,
                 out_bus_internal,
                 out_bus_external,
                 label):
        super().__init__(
                 nominal_power,
                 specific_generation,
                 funding,
                 out_bus_internal,
                 out_bus_external,
                 label)
