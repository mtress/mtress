# -*- coding: utf-8 -*-

"""
helper functions with background in physics

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""

import numpy as np

from ._constants import (
    H2_MOLAR_MASS,
    IDEAL_GAS_CONSTANT,
    rk_a,
    rk_b,
    SECONDS_PER_HOUR,
    ZERO_CELSIUS,
)


def kilo_to_mega(arg):
    """
    use to make explicit unit conversions instead of just dividing by 1000
    """
    return arg / 1000


def celsius_to_kelvin(arg):
    """
    converts °C to K
    """
    return ZERO_CELSIUS + arg


def kelvin_to_celsius(arg):
    """
    converts K to °C
    """
    return arg - ZERO_CELSIUS


def kJ_to_MWh(arg):  # pylint: disable=C0103
    """
    converts kJ to MWh
    """
    return kilo_to_mega(arg / SECONDS_PER_HOUR)


def bar_to_pascal(arg):
    """
    convert gas pressure from bar to pascals
    """
    return arg * 100000


def mean_logarithmic_temperature(t_high, t_low):
    """
    Logarithmic mean temperature as used by the
    Lorenz CIO Model

    :param t_high: High Temperature [K]
    :param t_low: Low Temperature [K]
    :return: Mean Logarithmic Temperature [K]
    """
    return (t_low - t_high) / np.log(t_low / t_high)


def lorenz_cop(temp_in, temp_out):
    """
    Calculate the theoretical COP of a infinite number
    of heat pump processes acc. to Lorenz 1895

    (Lorenz, H, 1895. Die Ermittlung der Grenzwerte der
    thermodynamischen Energieumwandlung. Zeitschrift für
    die gesammte Kälte-Industrie, 2(1-3, 6-12).)
    :param temp_in: Inlet Temperature
    :param temp_out: Outlet Temperature
    :return: Ideal COP
    """
    return temp_out / np.maximum(temp_out - temp_in, 1e-3)


def calc_cop(temp_input, temp_output, cop_0_35=4.6):
    """
    :param temp_input: Higher Temperature of the source (K)
    :param temp_output: Flow Temperature of the heating system (K)
    :param cop_0_35: COP for B0/W35
    :return: Scaled COP for the given temperatures
    """
    cpf = cop_0_35 / lorenz_cop(
        temp_in=celsius_to_kelvin(0), temp_out=celsius_to_kelvin(35)
    )

    cop = cpf * lorenz_cop(temp_in=temp_input, temp_out=temp_output)

    return cop


def calc_isothermal_compression_energy(p_in, p_out, T=20, R=4124.2, unit_conversion=1):
    r"""
    Calculate the energy demand to compress an ideal gas at constant temperature.

    This function calculates the energy demand for an isothermal compression
    of 1 kg of an ideal gas with gas constant R from pressure p_in to pressure
    p_out.

    The work required for isothermal compression from pressure level
    :math:`p_\mathrm{in}` to :math:`p_\mathrm{out}` at the temperature
    :math:`T` in Kelvin is given by
    .. math:: W = R \cdot T \cdot \ln \frac{p_\mathrm{out}}{p_\mathrm{in}} \,,

    where :math:`R` denotes the gas constant of the gas in question.

    :param p_in: Inlet pressure in bar
    :param p_out: Outlet pressure in bar
    :param T: Temperature in deg C, defaults to 20
    :param R: Gas constant in  J / (kg * K), defaults to 4124.2
    :param unit_conversion: If the gas flows is given in other unit for ex- KWh.
    :return: Energy required for compression in kWh
    """
    T += 273.15  # Convert temperature to Kelvin
    return (R * T * np.log(p_out / p_in) / (3600 * 1000)) / unit_conversion

def calc_hydrogen_density(pressure, temperature: float = 25) -> float:
    """
    Calculate the density of hydrogen gas.
    :param temperature: H2 gas temperature in the storage tank
    :param pressure: Pressure of hydrogen gas (in bar)
    :return: Density of hydrogen gas (in kilograms per cubic meter)
    """
    pressure = bar_to_pascal(pressure)
    gas_temperature = 273.15 + temperature
    a = rk_a  # Redlich-Kwong parameter 'a' for H2
    b = rk_b  # Redlich-Kwong parameter 'b' for H2
    v_spec = 10  # predefined initial value for specific volume [m³/mol]

    for i in range(10):
        v_spec = (
            IDEAL_GAS_CONSTANT * gas_temperature / (pressure
            + (a / (gas_temperature**0.5 * v_spec * (v_spec + b))))
        ) + b

    density = H2_MOLAR_MASS / v_spec

    return density
