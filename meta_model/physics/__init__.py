# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""

from ._helper_functions import (kilo_to_mega,
                                celsius_to_kelvin,
                                kelvin_to_celsius,
                                kJ_to_MWh,
                                mean_logarithmic_temperature,
                                lorenz_cop,
                                calc_cop)

from ._constants import (ZERO_CELSIUS,
                         HS_PER_HI_GAS,
                         HS_PER_HI_WP,
                         HHV_WP,
                         H2O_HEAT_CAPACITY,
                         H2O_HEAT_FUSION,
                         H2O_DENSITY,
                         TC_CONCRETE,
                         TC_INSULATION,
                         SECONDS_PER_HOUR)
