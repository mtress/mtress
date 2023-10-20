"""This module provide gas carrier in MTRESS"""

from oemof.solph import Bus, Flow

from .._abstract_component import AbstractSolphRepresentation
from ._abstract_carrier import AbstractLayeredGasCarrier
from dataclasses import dataclass
from ..physics import (
    calc_biogas_heating_value,
    CH4_LHV,
    CH4_HHV,
    CH4_MOLAR_MASS,
    H2_MOLAR_MASS,
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
    LHV=33.3,
    HHV=39.4,
    molar_mass=H2_MOLAR_MASS,
)

# By default natural gas contains methane(90%), ethane(5%),
# propane(3%), butane (2%), other impurities are ignored
NATURAL_GAS = Gas(
    name="NaturalGas",
    LHV=13,
    HHV=14.5,
    molar_mass=calc_natural_gas_molar_mass(CH4_share=0.9, C2H6_share=0.5,
                                           C3H8_share=0.3, C4H10_share=0.2),
)

# Biogas in default has 75% CH4 and 25% CO2, other impurity gases
# are ignored.
BIOGAS = Gas(
    name="Biogas",
    LHV=calc_biogas_heating_value(heating_value=CH4_LHV),
    HHV=calc_biogas_heating_value(heating_value=CH4_HHV),
    molar_mass=calc_biogas_molar_mass(CH4_share=0.75, C0_2_share=0.25),
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

class GasCarrier(AbstractLayeredGasCarrier, AbstractSolphRepresentation):
    """
    GasCarrier is the container for different types of gases, which
    considers the gas properties from dataclass Gas. All gas flows
    be it Hydrogen, Natural gas, Biogas or Bio-Methane are considered
    to be in kg to maintain resiliency in the modelling.
    """

    def __init__(
        self,
        gases: dict,
    ):
        super().__init__(gas_type=gases.keys(), pressures=gases.values())
        self.gases = gases
        self.distribution = {}

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        for gas, pressure_levels in self.gases.items():
            pressure_low = None
            self.distribution[gas] = {}
            for pressure in pressure_levels:
                # Check if this is the first bus for this gas
                if not self.distribution[gas]:
                    bus = self.create_solph_node(
                        label=f"{gas.name}_out_{pressure}",
                        node_type=Bus,
                    )
                else:
                    bus = self.create_solph_node(
                        label=f"{gas.name}_out_{pressure}",
                        node_type=Bus,
                        outputs={self.distribution[gas][pressure_low]: Flow()},
                    )
                self.distribution[gas][pressure] = bus

                # prepare for the next iteration of the loop
                pressure_low = pressure

    @property
    def inputs(self):
        return self.distribution

    @property
    def outputs(self):
        return self.distribution

    @property
    def pressures(self):
        return self.pressure_levels

    @property
    def gas(self):
        return self.gas_type
