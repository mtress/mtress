# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""

from ._constants import (
    H2_HHV,
    H2_LHV,
    H2O_DENSITY,
    H2O_HEAT_CAPACITY,
    H2O_HEAT_FUSION,
    HHV_WP,
    HS_PER_HI_GAS,
    HS_PER_HI_WP,
    SECONDS_PER_HOUR,
    TC_CONCRETE,
    TC_INSULATION,
    ZERO_CELSIUS,
)
from ._helper_functions import (
    calc_cop,
    calc_isothermal_compression_energy,
    celsius_to_kelvin,
    kelvin_to_celsius,
    kilo_to_mega,
    kJ_to_MWh,
    lorenz_cop,
    mean_logarithmic_temperature,
)

__all__ = [
    "kilo_to_mega",
    "celsius_to_kelvin",
    "kelvin_to_celsius",
    "kJ_to_MWh",
    "mean_logarithmic_temperature",
    "lorenz_cop",
    "calc_cop",
    "ZERO_CELSIUS",
    "HS_PER_HI_GAS",
    "HS_PER_HI_WP",
    "HHV_WP",
    "H2O_HEAT_CAPACITY",
    "H2O_HEAT_FUSION",
    "H2O_DENSITY",
    "H2_LHV",
    "H2_HHV",
    "TC_CONCRETE",
    "TC_INSULATION",
    "SECONDS_PER_HOUR",
    "calc_isothermal_compression_energy",
]
