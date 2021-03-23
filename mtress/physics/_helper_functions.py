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

from ._constants import (SECONDS_PER_HOUR, ZERO_CELSIUS)


def kilo_to_mega(arg):
    """
    use to make explicit unit conversions instead of just dividing by 1000
    """
    return arg/1000


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


def calc_cop(temp_input,
             temp_output,
             cop_0_35=4.6):
    """
    :param temp_input: Higher Temperature of the source (K)
    :param temp_output: Flow Temperature of the heating system (K)
    :param cop_0_35: COP for B0/W35
    :return: Scaled COP for the given temperatures
    """
    cpf = cop_0_35 / lorenz_cop(temp_in=celsius_to_kelvin(0),
                                temp_out=celsius_to_kelvin(35))

    cop = cpf * lorenz_cop(temp_in=temp_input,
                           temp_out=temp_output)

    return cop
