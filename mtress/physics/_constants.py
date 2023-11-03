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
NG_LHV = 13  # kWh/kg
NG_HHV = 14.5  # kWh/kg
C2H6_MOLAR_MASS = 0.03007  # kg/mol
C3H8_MOLAR_MASS = 0.0441   # kg/mol
C4H10_MOLAR_MASS = 0.0582  # kg/mol

# Biogas
CH4_MOLAR_MASS = 0.01604  # kg/mol
CO2_MOLAR_MASS = 0.04401  # kg/mol
CH4_HHV = 15.4  # Kwh/kg
CH4_LHV = 13.9  # Kwh/kg

# Wood pellets
HS_PER_HI_WP = 1.08  # according to DIN V 18599
# higher heating value(?)
HHV_WP = 4.8  # kWh/kg  /  MWh/t

# Water in heat storage
H2O_HEAT_CAPACITY = 4.182  # kJ/(kg*K)
H2O_HEAT_FUSION = 0.09265  # MWh/t, = 333.55 J/g
H2O_DENSITY = 1000  # kg/m^3

# Hydrogen
H2_LHV = 33.33  # kWh/kg
H2_HHV = 39.41  # kWh/kg
H2_MOLAR_MASS = 0.00201588  # kg/mol
IDEAL_GAS_CONSTANT = 8.314  # J/(mol·K)
rk_a = 0.1428  # Redlich-Kwong parameter 'a' for H2
rk_b = 1.8208 * 10**-5  # Redlich-Kwong parameter 'b' for H2
# Thermal conductivity
TC_CONCRETE = 0.8  # W / (m * K)
TC_INSULATION = 0.04  # W / (m * K)

# improve readability, used e.g. for J -> Wh
SECONDS_PER_HOUR = 3600
