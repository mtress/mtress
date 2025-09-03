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
import pandas as pd

from ._constants import SECONDS_PER_HOUR, ZERO_CELSIUS


def one_to_mega(arg):
    """
    use to make explicit unit conversions instead of just dividing by 1000000
    """
    return arg / 1000000


def mega_to_one(arg):
    """
    use to make explicit unit conversions instead of just
    multiplying by 1000000
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


def logarithmic_mean_temperature(temp_high, temp_low):
    """
    Logarithmic mean temperature difference as used by the
    Lorenz CIO Model

    :param t_high: High Temperature (in K)
    :param t_low: Low Temperature (in K)
    :return: Logarithmic Mean Temperature Difference (in K)
    """
    if temp_high < 0 or temp_low < 0:
        raise ValueError("Temperatures in Kelvin cannot be negative.")
    return (temp_low - temp_high) / np.log(temp_low / temp_high)


def lorenz_cop(temp_low, temp_high):
    """
    Calculate the theoretical COP of a infinite number
    of heat pump processes acc. to Lorenz 1895

    (Lorenz, H, 1895. Die Ermittlung der Grenzwerte der
    thermodynamischen Energieumwandlung. Zeitschrift für
    die gesammte Kälte-Industrie, 2(1-3, 6-12).)
    :param temp_low: Inlet Temperature (in K)
    :param temp_high: Outlet Temperature (in K)
    :return: Ideal COP
    """
    if temp_high < 0 or temp_low < 0:
        raise ValueError("Temperatures in Kelvin cannot be negative.")
    return temp_high / np.maximum(temp_high - temp_low, 1e-3)


def calc_cop(
    ref_cop,
    temp_primary_in: float = None,
    temp_secondary_out: float = None,
    temp_primary_out: float = None,
    temp_secondary_in: float = None,
):
    """
    :param ref_cop: Data class representing the reference COP
    :param temp_primary_in: Inlet temperature in the primary side (in °C)
    :param temp_secondary_out: Outlet temperature in the secondary side (in °C)
    :param temp_primary_out: Outlet temperature in the primary side (in °C)
    :param temp_secondary_in: Inlet temperature in the secondary side (in °C)
    :return: Scaled COP for the given temperatures
    """

    temp_primary_in = celsius_to_kelvin(temp_primary_in)
    temp_secondary_out = celsius_to_kelvin(temp_secondary_out)

    if temp_primary_out is None or temp_primary_out == temp_primary_in:
        temp_low = temp_primary_in
    else:
        temp_primary_out = celsius_to_kelvin(temp_primary_out)
        temp_low = logarithmic_mean_temperature(
            temp_high=temp_primary_in, temp_low=temp_primary_out
        )

    if temp_secondary_in is None or temp_secondary_out == temp_secondary_in:
        temp_high = temp_secondary_out
    else:
        temp_secondary_in = celsius_to_kelvin(temp_secondary_in)
        temp_high = logarithmic_mean_temperature(
            temp_high=temp_secondary_out, temp_low=temp_secondary_in
        )

    # intermediate step: cop_design/lorenz_design
    cpf = ref_cop.cop / lorenz_cop(
        temp_low=logarithmic_mean_temperature(
            temp_high=celsius_to_kelvin(ref_cop.cold_side_in),
            temp_low=celsius_to_kelvin(ref_cop.cold_side_out),
        ),
        temp_high=logarithmic_mean_temperature(
            temp_high=celsius_to_kelvin(ref_cop.warm_side_out),
            temp_low=celsius_to_kelvin(ref_cop.warm_side_in),
        ),
    )
    # cop = cop_design * (lorenz_real/lorenz_design)
    cop = cpf * lorenz_cop(temp_low=temp_low, temp_high=temp_high)

    return cop


def calc_isothermal_compression_energy(p_in, p_out, T=20, R=4124.2):
    r"""
    Calculate the energy demand to compress an ideal gas at
    constant temperature.

    This function calculates the energy demand for an isothermal compression
    of 1 kg of an ideal gas with gas constant R from input_pressure p_in to
    input_pressure p_out.

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
    return R * celsius_to_kelvin(T) * np.log(p_out / p_in) / SECONDS_PER_HOUR

#simpler version 
def calc_cop_piecewise_2(
    ref_cop,
    temp_primary_in: float = None,
    temp_secondary_out: float = None,
    temp_primary_out: float = None,     # unused
    temp_secondary_in: float = None,
    ref_primary_in: float = None,
    ref_secondary_out: float = None,
    ref_primary_out: float = None,      # unused
    ref_secondary_in: float = None,
    options_cop: dict = {},
) -> float:
    """
    Calculates COP using a 3-var piecewise linear model:
    - Uses COTe_in, Ts_in, Ts_out
    - Interpolates between Ts_out = 35°C and 55°C equations
    - If ref_cop (class or float) and ref temps are provided, scales COP to match ref_cop

    :param options_cop: {cop_eqs}
    # TODO: Describe options_cop
    # TODO: describe inputs, remove unnecessary ones

    """

    def _cop_model(te_in, ts_in, ts_out):
        if te_in is None or ts_in is None or ts_out is None:
            return np.nan

        if te_in < 6:
            region = "lt6"
        elif te_in <= 10:
            region = "6_10"
        else:
            region = "gt10"

        if "cop_eqs" in options_cop:
            cop_eqs = options_cop["cop_eqs"]
        else:
            cop_eqs = {
                35: {
                    'lt6':   (0.0869, 0.0475, 0.0554, 0.0016),
                    '6_10': (0.1500, 0.0426, 0.0497, 0.0014),
                    'gt10': (0.0831, 0.0540, 0.0630, 0.0018),
                },
                55: {
                    'lt6':   (0.0637, 0.0209, 0.0230, 0.0004),
                    '6_10': (0.1100, 0.0187, 0.0206, 0.0004),
                    'gt10': (0.0598, 0.0232, 0.0255, 0.0005),
                },
            }

        a35, e35, f35, g35 = cop_eqs[35][region]
        a55, e55, f55, g55 = cop_eqs[55][region]

        alpha = (ts_out - 35) / 20
        a = (1 - alpha) * a35 + alpha * a55
        e = (1 - alpha) * e35 + alpha * e55
        f = (1 - alpha) * f35 + alpha * f55
        g = (1 - alpha) * g35 + alpha * g55

        return a * te_in + e * ts_in + f * ts_out + g

    model_cop = _cop_model(temp_primary_in, temp_secondary_in, temp_secondary_out)

    # Use reference temps from dataclass if not passed directly
    if ref_cop is not None:
        if hasattr(ref_cop, "cop"):
            if ref_primary_in is None:
                ref_primary_in = ref_cop.cold_side_in
            if ref_secondary_in is None:
                ref_secondary_in = ref_cop.warm_side_in
            if ref_secondary_out is None:
                ref_secondary_out = ref_cop.warm_side_out
            ref_cop_value = ref_cop.cop
        else:
            ref_cop_value = ref_cop  # in case it's a float

        # All ref temps must now be defined
        if None not in (ref_primary_in, ref_secondary_in, ref_secondary_out):
            model_ref_cop = _cop_model(ref_primary_in, ref_secondary_in, ref_secondary_out)
            if model_ref_cop and not np.isnan(model_ref_cop) and model_ref_cop != 0:
                scale = ref_cop_value / model_ref_cop
                return scale * model_cop

    return model_cop


def calc_cop_linear_3var(
    ref_cop,
    temp_primary_in: float = None,
    temp_secondary_out: float = None,
    temp_primary_out: float = None,     # unused
    temp_secondary_in: float = None,
    ref_primary_in: float = None,
    ref_secondary_out: float = None,
    ref_primary_out: float = None,      # unused
    ref_secondary_in: float = None,
    options_cop: dict = {},

) -> float:
    """
    Calculates COP using simplified 3-variable linear fit:
    COP = A·Te_in + E·Ts_in + F·Ts_out + G
    Linearly interpolates between:
      - Ts_out = 35°C (Fit 35°C)
      - Ts_out = 55°C (Fit 55°C)
    Optionally scales result to match reference COP.

    :param ref_cop: Data class representing the reference COP
    :param temp_primary_in: Inlet temperature in the primary side (in °C)
    :param temp_secondary_out: Outlet temperature in the secondary side (in °C)
    :param temp_primary_out: Outlet temperature in the primary side (in °C)
    :param temp_secondary_in: Inlet temperature in the secondary side (in °C)
    :param options_cop: {cop_eqs}
    #TODO: Describe options_cop
    """

    def _cop_model(te_in, ts_in, ts_out):
        if te_in is None or ts_in is None or ts_out is None:
            return np.nan

        # Your fitted coefficients:
        if "cop_eqs" in options_cop:
            cop_eqs = options_cop["cop_eqs"]
        else:
            cop_eqs = {
                35: (0.0850, 0.0526, 0.0613, 0.0018),  # A, E, F, G
                55: (0.0470, 0.0247, 0.0271, 0.0005),
                }

        a35, e35, f35, g35 = cop_eqs[35]
        a55, e55, f55, g55 = cop_eqs[55]

        alpha = (ts_out - 35) / 20  # interpolate from 35 to 55
        a = (1 - alpha) * a35 + alpha * a55
        e = (1 - alpha) * e35 + alpha * e55
        f = (1 - alpha) * f35 + alpha * f55
        g = (1 - alpha) * g35 + alpha * g55

        return a * te_in + e * ts_in + f * ts_out + g

    model_cop = _cop_model(temp_primary_in, temp_secondary_in, temp_secondary_out)

    # Optional scaling if reference COP is provided
    if ref_cop is not None:
        if hasattr(ref_cop, "cop"):
            if ref_primary_in is None:
                ref_primary_in = ref_cop.cold_side_in
            if ref_secondary_in is None:
                ref_secondary_in = ref_cop.warm_side_in
            if ref_secondary_out is None:
                ref_secondary_out = ref_cop.warm_side_out
            ref_cop_value = ref_cop.cop
        else:
            ref_cop_value = ref_cop

        if None not in (ref_primary_in, ref_secondary_in, ref_secondary_out):
            model_ref_cop = _cop_model(ref_primary_in, ref_secondary_in, ref_secondary_out)
            if model_ref_cop and not np.isnan(model_ref_cop) and model_ref_cop != 0:
                return (ref_cop_value / model_ref_cop) * model_cop

    return model_cop


#precise version 
# list of coefficients for the graphical representaiton of the COP variance with cold and warm side temperatures. These individual lines represent the gradient between the known points in the COP curve.
#equation format: COP = a*Te_in + d*Te_out + e*Ts_in + f*Ts_out + g
    """ This method uses a polynomial function (quadratic) to fit the cop curve of a real heat pump
    as a function of the four temperatures in the warm and cold sides of the hp
    :param ref_cop: Data class representing the reference COP
    :param temp_primary_in: Inlet temperature in the primary side (in °C)
    :param temp_secondary_out: Outlet temperature in the secondary side (in °C)
    :param temp_primary_out: Outlet temperature in the primary side (in °C)
    :param temp_secondary_in: Inlet temperature in the secondary side (in °C)
    :return: Scaled COP for the given temperatures """

coeff_list = [
    # Ts_in = 30  entries ...
    {"Ts_in": 30, "Te_start": -20, "Te_end": -15, "a": 0.10,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.60},
    {"Ts_in": 30, "Te_start": -15, "Te_end": -10, "a": 0.08,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.30},
    {"Ts_in": 30, "Te_start": -10, "Te_end":  -5, "a": 0.08,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.30},
    {"Ts_in": 30, "Te_start":  -5, "Te_end":   0, "a": 0.11,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.45},
    {"Ts_in": 30, "Te_start":   0, "Te_end":   5, "a": 0.06,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.45},
    {"Ts_in": 30, "Te_start":   5, "Te_end":   6, "a": 0.15,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.00},
    {"Ts_in": 30, "Te_start":   6, "Te_end":   7, "a": 0.20,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.70},
    {"Ts_in": 30, "Te_start":   7, "Te_end":   8, "a": 0.10,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.40},
    {"Ts_in": 30, "Te_start":   8, "Te_end":   9, "a": 0.20,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.60},
    {"Ts_in": 30, "Te_start":   9, "Te_end":  10, "a": 0.10,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.50},
    {"Ts_in": 30, "Te_start":  10, "Te_end":  11, "a": 0.20,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.50},
    {"Ts_in": 30, "Te_start":  11, "Te_end":  12, "a": 0.10,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.60},
    {"Ts_in": 30, "Te_start":  12, "Te_end":  13, "a": 0.20,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.40},
    {"Ts_in": 30, "Te_start":  13, "Te_end":  15, "a": 0.05,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 4.35},
    {"Ts_in": 30, "Te_start":  15, "Te_end":  20, "a": 0.06,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 4.20},
    {"Ts_in": 30, "Te_start":  20, "Te_end":  25, "a": 0.10,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.40},
    {"Ts_in": 30, "Te_start":  25, "Te_end":  30, "a": 0.10,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.40},
    {"Ts_in": 30, "Te_start":  30, "Te_end":  35, "a": 0.06,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 4.60},

    # Ts_in = 35 entries ...
    {"Ts_in": 35, "Te_start":  -7, "Te_end":  -6, "a": 0.085,   "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.10},
    {"Ts_in": 35, "Te_start":  -6, "Te_end":  -5, "a": 0.085,   "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.10},
    {"Ts_in": 35, "Te_start":  -5, "Te_end":  -4, "a": 0.1075,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.2125},
    {"Ts_in": 35, "Te_start":  -4, "Te_end":  -3, "a": 0.095,   "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.1625},
    {"Ts_in": 35, "Te_start":  -3, "Te_end":  -2, "a": 0.095,   "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.1625},
    {"Ts_in": 35, "Te_start":  -2, "Te_end":  -1, "a": 0.095,   "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.1625},
    {"Ts_in": 35, "Te_start":  -1, "Te_end":   0, "a": 0.095,   "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.1625},
    {"Ts_in": 35, "Te_start":   0, "Te_end":   1, "a": 0.0575,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.1625},
    {"Ts_in": 35, "Te_start":   1, "Te_end":   2, "a": 0.0700,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.1500},
    {"Ts_in": 35, "Te_start":   2, "Te_end":   3, "a": 0.0575,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.1750},
    {"Ts_in": 35, "Te_start":   3, "Te_end":   4, "a": 0.0575,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.1750},
    {"Ts_in": 35, "Te_start":   4, "Te_end":   5, "a": 0.0575,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.1750},
    {"Ts_in": 35, "Te_start":   5, "Te_end":   6, "a": 0.1375,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.7750},
    {"Ts_in": 35, "Te_start":   6, "Te_end":   7, "a": 0.20,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.4000},
    {"Ts_in": 35, "Te_start":   7, "Te_end":   8, "a": 0.0875,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.1875},
    {"Ts_in": 35, "Te_start":   8, "Te_end":   9, "a": 0.1625,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.5875},
    {"Ts_in": 35, "Te_start":   9, "Te_end":  10, "a": 0.1250,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.9250},
    {"Ts_in": 35, "Te_start":  10, "Te_end":  11, "a": 0.1625,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.5500},
    {"Ts_in": 35, "Te_start":  11, "Te_end":  12, "a": 0.0875,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.3750},
    {"Ts_in": 35, "Te_start":  12, "Te_end":  13, "a": 0.1625,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.4750},
    {"Ts_in": 35, "Te_start":  13, "Te_end":  15, "a": 0.0500,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.9375},
    {"Ts_in": 35, "Te_start":  15, "Te_end":  20, "a": 0.0600,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.7875},
    {"Ts_in": 35, "Te_start":  20, "Te_end":  25, "a": 0.0875,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.2375},
    {"Ts_in": 35, "Te_start":  25, "Te_end":  30, "a": 0.1000,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.9250},
    {"Ts_in": 35, "Te_start":  30, "Te_end":  35, "a": 0.0485,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 4.4700},

    # Ts_in = 40 entries ...
    {"Ts_in": 40, "Te_start":  -7, "Te_end":  -6, "a": 0.0900,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.9000},
    {"Ts_in": 40, "Te_start":  -6, "Te_end":  -5, "a": 0.0900,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.9000},
    {"Ts_in": 40, "Te_start":  -5, "Te_end":  -4, "a": 0.1050,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.9750},
    {"Ts_in": 40, "Te_start":  -4, "Te_end":  -3, "a": 0.0800,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.8750},
    {"Ts_in": 40, "Te_start":  -3, "Te_end":  -2, "a": 0.0800,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.8750},
    {"Ts_in": 40, "Te_start":  -2, "Te_end":  -1, "a": 0.0800,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.8750},
    {"Ts_in": 40, "Te_start":  -1, "Te_end":   0, "a": 0.0800,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.8750},
    {"Ts_in": 40, "Te_start":   0, "Te_end":   1, "a": 0.0550,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.8750},
    {"Ts_in": 40, "Te_start":   1, "Te_end":   2, "a": 0.0800,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.8500},
    {"Ts_in": 40, "Te_start":   2, "Te_end":   3, "a": 0.0550,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.9000},
    {"Ts_in": 40, "Te_start":   3, "Te_end":   4, "a": 0.0550,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.9000},
    {"Ts_in": 40, "Te_start":   4, "Te_end":   5, "a": 0.0550,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.9000},
    {"Ts_in": 40, "Te_start":   5, "Te_end":   6, "a": 0.1250,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.5500},
    {"Ts_in": 40, "Te_start":   6, "Te_end":   7, "a": 0.2000,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.1000},
    {"Ts_in": 40, "Te_start":   7, "Te_end":   8, "a": 0.0750,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.9750},
    {"Ts_in": 40, "Te_start":   8, "Te_end":   9, "a": 0.1250,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.5750},
    {"Ts_in": 40, "Te_start":   9, "Te_end":  10, "a": 0.1500,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.3500},
    {"Ts_in": 40, "Te_start":  10, "Te_end":  11, "a": 0.1250,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.6000},
    {"Ts_in": 40, "Te_start":  11, "Te_end":  12, "a": 0.0750,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.1500},
    {"Ts_in": 40, "Te_start":  12, "Te_end":  13, "a": 0.1250,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.5500},
    {"Ts_in": 40, "Te_start":  13, "Te_end":  15, "a": 0.0500,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.5250},
    {"Ts_in": 40, "Te_start":  15, "Te_end":  20, "a": 0.0600,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.3750},
    {"Ts_in": 40, "Te_start":  20, "Te_end":  25, "a": 0.0750,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.0750},
    {"Ts_in": 40, "Te_start":  25, "Te_end":  30, "a": 0.1000,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.4500},
    {"Ts_in": 40, "Te_start":  30, "Te_end":  35, "a": 0.0370,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 4.3400},

    # Ts_in = 45 entries ...
    {"Ts_in": 45, "Te_start":  -7, "Te_end":  -6, "a": 0.0950,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.7000},
    {"Ts_in": 45, "Te_start":  -6, "Te_end":  -5, "a": 0.0950,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.7000},
    {"Ts_in": 45, "Te_start":  -5, "Te_end":  -4, "a": 0.1025,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.7375},
    {"Ts_in": 45, "Te_start":  -4, "Te_end":  -3, "a": 0.0650,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.5875},
    {"Ts_in": 45, "Te_start":  -3, "Te_end":  -2, "a": 0.0650,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.5875},
    {"Ts_in": 45, "Te_start":  -2, "Te_end":  -1, "a": 0.0650,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.5875},
    {"Ts_in": 45, "Te_start":  -1, "Te_end":   0, "a": 0.0650,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.5875},
    {"Ts_in": 45, "Te_start":   0, "Te_end":   1, "a": 0.0525,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.5875},
    {"Ts_in": 45, "Te_start":   1, "Te_end":   2, "a": 0.0900,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.5500},
    {"Ts_in": 45, "Te_start":   2, "Te_end":   3, "a": 0.0525,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.6250},
    {"Ts_in": 45, "Te_start":   3, "Te_end":   4, "a": 0.0525,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.6250},
    {"Ts_in": 45, "Te_start":   4, "Te_end":   5, "a": 0.0525,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.6250},
    {"Ts_in": 45, "Te_start":   5, "Te_end":   6, "a": 0.1125,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.3250},
    {"Ts_in": 45, "Te_start":   6, "Te_end":   7, "a": 0.2000,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 1.8000},
    {"Ts_in": 45, "Te_start":   7, "Te_end":   8, "a": 0.0625,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.7625},
    {"Ts_in": 45, "Te_start":   8, "Te_end":   9, "a": 0.0875,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.5625},
    {"Ts_in": 45, "Te_start":   9, "Te_end":  10, "a": 0.1750,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 1.7750},
    {"Ts_in": 45, "Te_start":  10, "Te_end":  11, "a": 0.0875,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.6500},
    {"Ts_in": 45, "Te_start":  11, "Te_end":  12, "a": 0.0625,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.9250},
    {"Ts_in": 45, "Te_start":  12, "Te_end":  13, "a": 0.0875,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.6250},
    {"Ts_in": 45, "Te_start":  13, "Te_end":  15, "a": 0.0500,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 3.1125},
    {"Ts_in": 45, "Te_start":  15, "Te_end":  20, "a": 0.0600,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.9625},
    {"Ts_in": 45, "Te_start":  20, "Te_end":  25, "a": 0.0625,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.9125},
    {"Ts_in": 45, "Te_start":  25, "Te_end":  30, "a": 0.1000,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 1.9750},
    {"Ts_in": 45, "Te_start":  30, "Te_end":  35, "a": 0.0255,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 4.2100},

    # Ts_in = 50 entries ...
    {"Ts_in": 50, "Te_start":  -7, "Te_end":  -6, "a": 0.10,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.50},
    {"Ts_in": 50, "Te_start":  -6, "Te_end":  -5, "a": 0.10,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.50},
    {"Ts_in": 50, "Te_start":  -5, "Te_end":  -4, "a": 0.10,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.50},
    {"Ts_in": 50, "Te_start":  -4, "Te_end":  -3, "a": 0.05,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.30},
    {"Ts_in": 50, "Te_start":  -3, "Te_end":  -2, "a": 0.05,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.30},
    {"Ts_in": 50, "Te_start":  -2, "Te_end":  -1, "a": 0.05,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.30},
    {"Ts_in": 50, "Te_start":  -1, "Te_end":   0, "a": 0.05,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.30},
    {"Ts_in": 50, "Te_start":   0, "Te_end":   1, "a": 0.05,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.30},
    {"Ts_in": 50, "Te_start":   1, "Te_end":   2, "a": 0.10,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.25},
    {"Ts_in": 50, "Te_start":   2, "Te_end":   3, "a": 0.05,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.35},
    {"Ts_in": 50, "Te_start":   3, "Te_end":   4, "a": 0.05,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.35},
    {"Ts_in": 50, "Te_start":   4, "Te_end":   5, "a": 0.05,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.35},
    {"Ts_in": 50, "Te_start":   5, "Te_end":   6, "a": 0.10,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.10},
    {"Ts_in": 50, "Te_start":   6, "Te_end":   7, "a": 0.20,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 1.50},
    {"Ts_in": 50, "Te_start":   7, "Te_end":   8, "a": 0.05,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.55},
    {"Ts_in": 50, "Te_start":   8, "Te_end":   9, "a": 0.05,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.55},
    {"Ts_in": 50, "Te_start":   9, "Te_end":  10, "a": 0.20,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 1.20},
    {"Ts_in": 50, "Te_start":  10, "Te_end":  15, "a": 0.05,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.70},
    {"Ts_in": 50, "Te_start":  15, "Te_end":  20, "a": 0.06,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.55},
    {"Ts_in": 50, "Te_start":  20, "Te_end":  25, "a": 0.05,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 2.75},
    {"Ts_in": 50, "Te_start":  25, "Te_end":  30, "a": 0.10,    "d": 0.0, "e": 0.0, "f": 0.0, "g": 1.50},
    {"Ts_in": 50, "Te_start":  30, "Te_end":  35, "a": 0.0140,  "d": 0.0, "e": 0.0, "f": 0.0, "g": 4.0800},
]

# Build DataFrame once, at import time:
_piecewise_df = pd.DataFrame(
    coeff_list,
    columns=["Ts_in", "Te_start", "Te_end", "a", "d", "e", "f", "g"]
)


def _lookup_single(
    Ts_in_val: float,
    Te_in: float,
    Te_out: float,
    Ts_in: float,
    Ts_out: float,
) -> float:
    """
    Look up COP for exactly one Ts_in_val (30, 35, 40, 45, or 50). 
    1. Filter the DataFrame to rows where Ts_in column == Ts_in_val.  
    2. Among those, pick the single row whose [Te_start <= Te_in <= Te_end].  
    3. Return COP = a·Te_in + d·Te_out + e·Ts_in + f·Ts_out + g.  
    If no matching row, return NaN.
    """
    sub = _piecewise_df[_piecewise_df["Ts_in"] == Ts_in_val]
    if sub.empty:
        return np.nan

    mask = (sub["Te_start"] <= Te_in) & (sub["Te_end"] >= Te_in)
    candidate = sub[mask]
    if candidate.empty:
        return np.nan

    row = candidate.iloc[0]  # take the first (and only) matching row
    a = float(row["a"])
    d = float(row["d"])
    e = float(row["e"])
    f = float(row["f"])
    g = float(row["g"])
    return a * Te_in + d * Te_out + e * Ts_in + f * Ts_out + g


def calc_cop_piecewise(
    ref_cop,
    temp_primary_in: float = None,
    temp_secondary_out: float = None,
    temp_primary_out: float = None,
    temp_secondary_in: float = None,
    options_cop: dict = {}
    ):
    """
    Piecewise‐linear COP with extrapolation outside [30, 50]:
    
    1. If either cold‐side or warm‐side temps are missing, return NaN immediately.
    2. Let all_Ts = [30, 35, 40, 45, 50].  
       Let Ts = temp_secondary_in (the actual warm‐side inlet you passed).  
    3. If Ts exactly equals one of all_Ts, do a single lookup.  
    4. Otherwise, find:
         Ts_floor = max(all_Ts < Ts)  (if Ts < 30, we clamp Ts_floor = 30)
         Ts_ceil  = min(all_Ts > Ts)  (if Ts > 50, we clamp Ts_ceil  = 50)
       Then compute:
         cop_floor = _lookup_single(Ts_floor, temp_primary_in, temp_primary_out, Ts_floor, Ts_floor+5)
         cop_ceil  = _lookup_single(Ts_ceil,  temp_primary_in, temp_primary_out, Ts_ceil,  Ts_ceil + 5)
       Even if Ts is outside [30,50], Ts_floor/ Ts_ceil = (30,50) so this still runs.
    5. Finally, blend linearly in Ts‐space using α = (Ts – Ts_floor)/(Ts_ceil – Ts_floor).  
       Note: if Ts < 30, α is negative → extrapolation;  
             if Ts > 50, α > 1 → extrapolation.

    :param options_cop: {cop_eqs}
    #TODO: Describe options_cop

    """
    # 1) Guard against missing inputs
    if any(v is None for v in (temp_primary_in, temp_secondary_in,
                               temp_primary_out, temp_secondary_out)):
        return np.nan

    all_Ts = np.sort(_piecewise_df["Ts_in"].unique())  # array([30, 35, 40, 45, 50])
    Ts = float(temp_secondary_in)

    # 2) Determine Ts_floor and Ts_ceil for blending (allow extrapolation):
    if Ts <= all_Ts.min():
        Ts_floor = all_Ts.min()   # = 30
        Ts_ceil  = all_Ts.max()   # = 50
    elif Ts >= all_Ts.max():
        Ts_floor = all_Ts.min()   # = 30
        Ts_ceil  = all_Ts.max()   # = 50
    else:
        Ts_floor = all_Ts[all_Ts < Ts].max()
        Ts_ceil  = all_Ts[all_Ts > Ts].min()

    # 3) If Ts exactly equals a discrete table level, we can use that alone:
    if Ts in all_Ts:
        return _lookup_single(
            Ts,
            temp_primary_in,
            temp_primary_out,
            Ts,
            temp_secondary_out,
        )

    # 4) Otherwise, compute COP at floor and ceil (this works even if Ts<30 or Ts>50):
    cop_floor = _lookup_single(
        Ts_floor,
        temp_primary_in,
        temp_primary_out,
        Ts_floor,
        Ts_floor + 5.0
    )
    cop_ceil = _lookup_single(
        Ts_ceil,
        temp_primary_in,
        temp_primary_out,
        Ts_ceil,
        Ts_ceil + 5.0
    )

    # If either lookup failed, return NaN
    if np.isnan(cop_floor) or np.isnan(cop_ceil):
        return np.nan

    # 5) Blend (or extrapolate) linearly in Ts‐space:
    alpha = (Ts - Ts_floor) / (Ts_ceil - Ts_floor)
    return (1 - alpha) * cop_floor + alpha * cop_ceil

