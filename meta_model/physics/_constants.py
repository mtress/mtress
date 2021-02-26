# -*- coding: utf-8 -*-

"""
physical constants

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""

# 0°C in K
ZERO_CELSIUS = 273.15  # K

# Natural gas
HS_PER_HI_GAS = 1.11  # according to DIN V 18599

# Wood pellets
HS_PER_HI_WP = 1.08  # according to DIN V 18599
# higher heating value(?)
HHV_WP = 4.8  # kWh/kg  /  MWh/t

# Water in heat storage
H2O_HEAT_CAPACITY = 4.182  # kJ/(kg*K)
H2O_HEAT_FUSION = 0.09265  # MWh/t, = 333.55 J/g
H2O_DENSITY = 1000  # Kg/m^3

# Thermal conductivity
TC_CONCRETE = 0.8  # W / (m * K)
TC_INSULATION = 0.04  # W / (m * K)

# improve readability, used e.g. for J -> Wh
SECONDS_PER_HOUR = 3600
