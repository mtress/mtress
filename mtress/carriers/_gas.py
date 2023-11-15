"""This module provide gas carrier in MTRESS"""


from oemof.solph import Bus, Flow

from .._abstract_component import AbstractSolphRepresentation
from ._abstract_carrier import AbstractLayeredCarrier


class GasCarrier(AbstractLayeredCarrier, AbstractSolphRepresentation):
    """
    GasCarrier is the container for different types of gases, which
    considers the gas properties from dataclass Gas. All gas flows
    be it Hydrogen, Natural gas, Biogas or Bio-Methane are considered
    to be in kg to maintain resiliency in the modelling.
    """

    def __init__(self, *, gases, **kwargs):
        """Initialize carrier."""
        super().__init__(levels=gases, **kwargs)

        self.distribution = {}

    def get_surrounding_levels(self, gas, pressure_level):
        """Get the next bigger and smaller level for the specified gas."""
        return AbstractLayeredCarrier._get_surrounding_levels(
            pressure_level, self._levels[gas]
        )

    @property
    def pressure_levels(self):
        """Return input_pressure level of gas carrier"""
        return self._levels

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        for gas, pressures in self.levels.items():
            pressure_low = None
            self.distribution[gas] = {}
            for pressure in pressures:
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
