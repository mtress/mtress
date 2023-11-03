"""
Different types of gases are defined here with its specific
parameter values.
"""

from dataclasses import dataclass

from ._constants import (
    CH4_MOLAR_MASS,
    CH4_LHV,
    CH4_HHV,
    H2_MOLAR_MASS,
    H2_HHV,
    H2_LHV,
    NG_HHV,
    NG_LHV,
)
from ._helper_functions import (
    calc_biogas_heating_value,
    calc_biogas_molar_mass,
    calc_natural_gas_molar_mass,
)


@dataclass
class Gas:
    """
    Here we provide the gas properties for some predefined
    gases such as Hydrogen, Natural Gas, Biogas, and Bio-methane.
    User can define its own gas by creating an object of the
    specific gas via this dataclass.
    """
    name: str
    # Heating value Kwh/kg
    LHV: float
    HHV: float
    # molar mass of gas, given in kg/mol
    molar_mass: float

    def __hash__(self):
        return hash((self.name, self.LHV, self.HHV, self.molar_mass))


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
    molar_mass=calc_natural_gas_molar_mass(),
)

BIOGAS = Gas(
    name="Biogas",
    LHV=calc_biogas_heating_value(),
    HHV=calc_biogas_heating_value(),
    molar_mass=calc_biogas_molar_mass(),
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
