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
    CH4_LHV,
    CH4_HHV,
    CH4_MOLAR_MASS,
    CO2_MOLAR_MASS,
    C2H6_MOLAR_MASS,
    C3H8_MOLAR_MASS,
    C4H10_MOLAR_MASS,
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
    convert gas input_pressure from bar to pascals
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

    :param p_in: Inlet input_pressure in bar
    :param p_out: Outlet input_pressure in bar
    :param T: Temperature in deg C, defaults to 20
    :param R: Gas constant in  J / (kg * K), defaults to 4124.2
    :return: Energy required for compression in kWh
    """
    T += 273.15  # Convert temperature to Kelvin
    return R * T * np.log(p_out / p_in) / (3600 * 1000)


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
            IDEAL_GAS_CONSTANT
            * gas_temperature
            / (pressure + (a / (gas_temperature**0.5 * v_spec * (v_spec + b))))
        ) + b

    density = H2_MOLAR_MASS / v_spec

    return density


def calc_biogas_heating_value(CH4_share=0.75, CO2_share=0.25, heating_value=CH4_LHV):
    """
    Calculate the heating value of biogas based on methane proportion.
    Heating value either LHV or HHV are calculated based on per kg
    i.e. KWh/kg

    :param CH4_share: Share proportion of methane in biogas
    :param CO2_share: Share proportion content of carbon-dioxide in biogas
    :param heating_value of methane, default LHV.
    """
    return (
        (CH4_share * CH4_MOLAR_MASS)
        / (CH4_share * CH4_MOLAR_MASS + CO2_share * CO2_MOLAR_MASS)
    ) * heating_value


def calc_biogas_molar_mass(CH4_share=0.75, C0_2_share=0.25):
    """
    This function calculates the molar mass of biogas depending on the
    gas proportion and its molar mass (kg/mol). Only methane and carbon-dioxide
    gas are considered and other impurities are ignored for this calculation.
    :param CH4_share: Share proportion of methane in biogas
    :param C0_2_share: Share proportion content of carbon-dioxide in biogas
    """
    return (CH4_share * CH4_MOLAR_MASS) + (C0_2_share * CO2_MOLAR_MASS)

def calc_natural_gas_molar_mass(
    CH4_share=0.9, C2H6_share=0.5, C3H8_share=0.3, C4H10_share=0.2
):
    """
    Calculate the molar mass of the natural gas depending on different
    gases present and its proportions. In most cases following gas exists:
    Methane, ethane, propane, butane, and  other impurities. Other impurity
    gases are ignored for this calculation.
    """
    return (
        (CH4_share * CH4_MOLAR_MASS)
        + (C2H6_share * C2H6_share)
        + (C3H8_share * C3H8_MOLAR_MASS)
        + (C4H10_share * CH4_MOLAR_MASS)
    )
