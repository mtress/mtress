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

from ._constants import SECONDS_PER_HOUR, ZERO_CELSIUS


def one_to_mega(arg):
    """
    use to make explicit unit conversions instead of just dividing by 1000000
    """
    return arg / 1000000

def mega_to_one(arg):
    """
    use to make explicit unit conversions instead of just multiplying by 1000000
    """
    return arg * 1000000


def one_to_kilo(arg):
    """
    use to make explicit unit conversions instead of just dividing by 1000
    """
    return arg / 1000


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
    convert gas input_pressure from bar to pascals
    """
    return arg * 100000


def mean_logarithmic_temperature(t_high, t_low):
    """
    Logarithmic mean temperature as used by the
    Lorenz CIO Model

    :param t_high: High Temperature (in K)
    :param t_low: Low Temperature (in K)
    :return: Mean Logarithmic Temperature (in K)
    """
    return (t_low - t_high) / np.log(t_low / t_high)


def lorenz_cop(temp_in, temp_out):
    """
    Calculate the theoretical COP of a infinite number
    of heat pump processes acc. to Lorenz 1895

    (Lorenz, H, 1895. Die Ermittlung der Grenzwerte der
    thermodynamischen Energieumwandlung. Zeitschrift für
    die gesammte Kälte-Industrie, 2(1-3, 6-12).)
    :param temp_in: Inlet Temperature (in K?)
    :param temp_out: Outlet Temperature (in K?)
    :return: Ideal COP
    """
    return temp_out / np.maximum(temp_out - temp_in, 1e-3)


def calc_cop(temp_input, temp_output, cop_0_35=4.6):
    """
    :param temp_input: Higher Temperature of the source (in K)
    :param temp_output: Flow Temperature of the heating system (in K)
    :param cop_0_35: COP for B0/W35
    :return: Scaled COP for the given temperatures
    """
    cpf = cop_0_35 / lorenz_cop(
        temp_in=celsius_to_kelvin(0), temp_out=celsius_to_kelvin(35)
    )

    cop = cpf * lorenz_cop(temp_in=temp_input, temp_out=temp_output)

    return cop


def calc_isothermal_compression_energy(p_in, p_out, T=20, R=4124.2):
    r"""
    Calculate the energy demand to compress an ideal gas at constant temperature.

    This function calculates the energy demand for an isothermal compression
    of 1 kg of an ideal gas with gas constant R from input_pressure p_in to input_pressure
    p_out.

    The work required for isothermal compression from input_pressure level
    :math:`p_\mathrm{in}` to :math:`p_\mathrm{out}` at the temperature
    :math:`T` in Kelvin is given by
    .. math:: W = R \cdot T \cdot \ln \frac{p_\mathrm{out}}{p_\mathrm{in}} \,,

    where :math:`R` denotes the gas constant of the gas in question.

    :param p_in: Inlet input_pressure (in bar)
    :param p_out: Outlet input_pressure (in bar)
    :param T: Temperature (in °C), by default to 20 °C
    :param R: Gas constant ( in J/(kg * K)), by default to 4124.2 J/(kg * K)
    :return: Energy required for compression (in Wh)
    """
    T += 273.15  # Convert temperature to Kelvin
    return R * celsius_to_kelvin(T) * np.log(p_out / p_in) / SECONDS_PER_HOUR



