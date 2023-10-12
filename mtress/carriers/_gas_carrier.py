"""This module provide gas carrier in MTRESS"""

from oemof.solph import Bus, Flow

from .._abstract_component import AbstractSolphRepresentation
from ._abstract_carrier import AbstractLayeredCarrier, AbstractLayeredGasCarrier
from dataclasses import dataclass


@dataclass
class Gas:
    """
    Here we provide the gas properties for some predefined
    gases such as Hydrogen, Natural Gas, Biogas, etc. User
    can define its own gas by creating an object of the gas
    via this dataclass.
    """
    # Energy per kg
    name: str
    energy: float

    # Gas constant in  J / (kg * K), for Hydrogen its 4124.2
    gas_constant: float

    def __hash__(self):
        # You can define a custom hash based on the attributes you want
        return hash((self.name, self.energy, self.gas_constant))


HYDROGEN = Gas(name="Hydrogen", energy=33.3, gas_constant=4124.2)
NATURAL_GAS = Gas(name="NaturalGas", energy=11, gas_constant=518.28)
BIOGAS = Gas(name="Biogas", energy=6.6, gas_constant=518.28)


class GasCarrier(AbstractLayeredGasCarrier, AbstractSolphRepresentation):
    """
    GasCarrier is the container for different types of gases, which
    considers the gas properties from dataclass Gas.
    """

    def __init__(
            self,
            gases: dict,
    ):
        super().__init__(gas_type=[*gases.keys()], pressures=[*gases.values()])
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
