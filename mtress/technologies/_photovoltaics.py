# -*- coding: utf-8 -*-

"""
pv wrapper for generic RenewableElectricitySource

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

from feedinlib.models.geometric_solar import solar_angles

from ._renewable_electricity_source import RenewableElectricitySource


class Photovoltaics(RenewableElectricitySource):
    """
    photovoltaics wrapper for generic RenewableElectricitySource
    """
    def __init__(self,
                 nominal_power,
                 tilt,
                 surface_azimuth,
                 latitude,
                 longitude,
                 funding,
                 out_bus_internal,
                 out_bus_external,
                 label,
                 energy_system):
        specific_generation = solar_angles(energy_system.timeindex,
                                           tilt,
                                           surface_azimuth,
                                           latitude,
                                           longitude)
        super().__init__(
                 nominal_power,
                 specific_generation,
                 funding,
                 out_bus_internal,
                 out_bus_external,
                 label,
                 energy_system)
