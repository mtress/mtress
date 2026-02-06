"""This module provide gas carrier in MTRESS"""

from oemof.solph import Bus, Flow

from ._abstract_carrier import AbstractLayeredCarrier
from .._constants import EnergyType


class GasCarrier(AbstractLayeredCarrier):
    """
    GasCarrier is the container for different types of gases, which
    considers the gas properties from dataclass Gas. All gas flows,
    be it Hydrogen, Natural gas, Biogas or Bio-Methane, are considered
    to be in kg to maintain resiliency in the modelling.

    Parameters
    ----------
    gas: in kg
    pressure: in bar
    """

    def __init__(
        self,
        *,
        location=None,
        custom_properties=None,
    ):
        """Initialize carrier."""
        super().__init__(
            location=location,
            custom_properties=custom_properties,
        )

        self.distribution = {}

        self._build_core()

    def get_surrounding_levels(self, gas, pressure_level):
        """Get the next bigger and smaller level for the specified gas."""
        return self._get_surrounding_levels(pressure_level, self._levels[gas])

    @property
    def pressure_levels(self):
        """Return input_pressure level of gas carrier"""
        return self._levels

    def _build_core(self):
        """Build core structure of oemof.solph representation."""

        self.inbound_interfaces[EnergyType.GAS] = self.subnodes
        self.outbound_interfaces[EnergyType.GAS] = self.subnodes

    @property
    def inputs(self):
        return self.distribution

    @property
    def outputs(self):
        return self.distribution

    def establish_interconnections(self):
        pass
