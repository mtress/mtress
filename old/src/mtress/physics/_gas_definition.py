"""
Different types of gases are defined here with its specific
parameter values. Various functions for gases are defined
here.
"""

from dataclasses import dataclass

from ._constants import IDEAL_GAS_CONSTANT
from ._helper_functions import bar_to_pascal

# Some parameters for different gases are given below

# Natural gas
HS_PER_HI_GAS = 1.11  # according to DIN V 18599
NG_LHV = 13000  # Wh/kg
NG_HHV = 14500  # Wh/kg
C2H6_MOLAR_MASS = 0.03007  # kg/mol
C3H8_MOLAR_MASS = 0.0441  # kg/mol
C4H10_MOLAR_MASS = 0.0582  # kg/mol

# Biogas
CH4_MOLAR_MASS = 0.01604  # kg/mol
CO2_MOLAR_MASS = 0.04401  # kg/mol
CH4_HHV = 15400  # Wh/kg
CH4_LHV = 13900  # Wh/kg


# Hydrogen
H2_LHV = 33330  # Wh/kg
H2_HHV = 39410  # Wh/kg
H2_MOLAR_MASS = 0.00201588  # kg/mol
rk_a = 0.1428  # Redlich-Kwong parameter 'a' for H2 in (m³bar/mol²)
rk_b = 1.8208 * 10**-5  # Redlich-Kwong parameter 'b' for H2 in (m³/mol)


def calc_hydrogen_density(pressure, temperature: float = 25) -> float:
    """
    Calculate the density of hydrogen gas.
    :param temperature: H2 gas temperature in the storage tank (in °C)
    :param pressure: Pressure of hydrogen gas (in bar)
    :return: Density of hydrogen gas (in kg/m³)
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


def calc_biogas_heating_value(
    CH4_share=0.75, CO2_share=0.25, heating_value=CH4_LHV
):
    """
    Calculate the heating value of biogas based on methane proportion.
    Heating value either LHV or HHV are calculated based on per kg
    i.e. KWh/kg

    :param CH4_share: Share proportion of methane in biogas
    :param CO2_share: Share proportion content of carbon-dioxide in biogas
    :param heating_value of methane: default LHV (in Wh/kg)
    :return: heating value in Wh
    """
    return (
        (CH4_share * CH4_MOLAR_MASS)
        / (CH4_share * CH4_MOLAR_MASS + CO2_share * CO2_MOLAR_MASS)
    ) * heating_value

def molar_mass(
    molar_masses: dict, 
    shares: dict, 
    tolerance: float = 1e-3
    ):
    "Calculates the molar mass for a compound from that of its constituents."
    if set(molar_masses.keys()) != set(shares.keys()):
        raise ValueError('The input sizes must match.')
    if abs(sum(shares.values())-1.0) > tolerance:
        raise ValueError('Shares must add up to one.')
    return sum(molar_masses[key]*shares[key] for key in molar_masses.keys())


@dataclass(frozen=True)
class Gas:
    """
    Here we provide the gas properties for some predefined
    gases such as Hydrogen, Natural Gas, Biogas, and Bio-methane.
    User can define its own gas by creating an object of the
    specific gas via this dataclass.
    """

    name: str
    # Heating value Wh/kg
    LHV: float
    HHV: float
    # molar mass of gas, given in kg/mol
    molar_mass: float

# Object of different predefined gases

HYDROGEN = Gas(
    name="Hydrogen",
    LHV=H2_LHV,
    HHV=H2_HHV,
    molar_mass=H2_MOLAR_MASS,
)

NATURAL_GAS = Gas(
    name="NaturalGas",
    LHV=NG_LHV,
    HHV=NG_HHV,
    molar_mass=molar_mass(
        molar_masses={
            'CH4': CH4_MOLAR_MASS, 
            'C2H6': C2H6_MOLAR_MASS, 
            'C3H8': C3H8_MOLAR_MASS, 
            'C4H10': C4H10_MOLAR_MASS
            }, 
        shares={
            'CH4': 0.9, 
            'C2H6': 0.05, 
            'C3H8': 0.03, 
            'C4H10': 0.02
            }
        )
)

BIOGAS = Gas(
    name="Biogas",
    LHV=calc_biogas_heating_value(heating_value=CH4_LHV),
    HHV=calc_biogas_heating_value(heating_value=CH4_HHV),
    molar_mass=molar_mass(
        molar_masses={
            'CH4': CH4_MOLAR_MASS, 
            'CO2': CO2_MOLAR_MASS
            }, 
        shares={
            'CH4': 0.75, 
            'CO2': 0.25
            }
        )
)

# Bio-methane is primarily considered to have methane and other impurities
# are ignored for calculation here. However, it's important to note that
# the exact composition of bio-methane can vary depending on the feedstock
# and the specific production process, and it may contain trace impurities
# and other gases. To get a more precise value for a specific bio-methane
# source, you would need to know its exact composition.
BIO_METHANE = Gas(
    name="BioMethane",
    LHV=CH4_LHV,
    HHV=CH4_HHV,
    molar_mass=CH4_MOLAR_MASS,
)
