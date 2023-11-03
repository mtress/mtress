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
    NG_HHV,
    NG_LHV,
    CH4_MOLAR_MASS,
    CO2_MOLAR_MASS,
    CH4_LHV,
    CH4_HHV,
    C2H6_MOLAR_MASS,
    C3H8_MOLAR_MASS,
    C4H10_MOLAR_MASS,
    H2_MOLAR_MASS,
    H2O_DENSITY,
    H2O_HEAT_CAPACITY,
    H2O_HEAT_FUSION,
    HHV_WP,
    HS_PER_HI_GAS,
    HS_PER_HI_WP,
    IDEAL_GAS_CONSTANT,
    rk_a,
    rk_b,
    SECONDS_PER_HOUR,
    TC_CONCRETE,
    TC_INSULATION,
    ZERO_CELSIUS,
)
from ._helper_functions import (
    bar_to_pascal,
    calc_cop,
    calc_hydrogen_density,
    calc_isothermal_compression_energy,
    calc_biogas_heating_value,
    calc_biogas_molar_mass,
    calc_natural_gas_molar_mass,
    celsius_to_kelvin,
    kelvin_to_celsius,
    kilo_to_mega,
    kJ_to_MWh,
    lorenz_cop,
    mean_logarithmic_temperature,
)

from ._gas_defination import (
    Gas,
    HYDROGEN,
    NATURAL_GAS,
    BIO_METHANE,
    BIOGAS,
)

__all__ = [
    "kilo_to_mega",
    "celsius_to_kelvin",
    "kelvin_to_celsius",
    "kJ_to_MWh",
    "bar_to_pascal",
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
    "NG_HHV",
    "NG_LHV",
    "NG_HHV",
    "CH4_MOLAR_MASS",
    "CO2_MOLAR_MASS",
    "CH4_LHV",
    "CH4_HHV",
    "C2H6_MOLAR_MASS",
    "C3H8_MOLAR_MASS",
    "C4H10_MOLAR_MASS",
    "H2_MOLAR_MASS",
    "IDEAL_GAS_CONSTANT",
    "rk_a",
    "rk_b",
    "TC_CONCRETE",
    "TC_INSULATION",
    "SECONDS_PER_HOUR",
    "calc_isothermal_compression_energy",
    "calc_hydrogen_density",
    "calc_biogas_heating_value",
    "Gas",
    "HYDROGEN",
    "NATURAL_GAS",
    "BIO_METHANE",
    "BIOGAS",
]
