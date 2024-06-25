"""This module provides ResistiveHeater component (power to heat)"""

import logging

from oemof.solph import Flow
from oemof.solph.components import Converter

from .._abstract_component import AbstractSolphRepresentation
from ..carriers import ElectricityCarrier, HeatCarrier
from ._abstract_technology import AbstractTechnology

LOGGER = logging.getLogger(__file__)


class ResistiveHeater(AbstractTechnology, AbstractSolphRepresentation):
    """
    ResistiveHeater converts electricity into heat at a given efficiency.
    """

    def __init__(
        self,
        name: str,
        nominal_power: float,
        maximum_temperature: float,
        minimum_temperature: float = 0,
        efficiency: float = 1,
    ):
        """
        Initialize ResistiveHeater.

        :param name: Set the name of the component.
        :param nominal_power: Nominal heating capacity of the heating rod (in W)
        :parma maximum_temperature: Temperature (in °C) of the heat output.
        :parma minimum_temperature: Lowest possible temperature (in °C) of the inlet.
        :param efficiency: Thermal conversion efficiency.
        """
        super().__init__(name=name)

        self.nominal_power = nominal_power
        self.maximum_temperature = maximum_temperature
        self.minimum_temperature = minimum_temperature
        self.efficiency = efficiency

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        # Add electrical connection
        electricity_carrier = self.location.get_carrier(ElectricityCarrier)
        electrical_bus = electricity_carrier.distribution

        # Add heat connection
        heat_carrier = self.location.get_carrier(HeatCarrier)

        heat_bus_warm, heat_bus_cold, ratio = heat_carrier.get_connection_heat_transfer(
            self.maximum_temperature, self.minimum_temperature
        )

        self.create_solph_node(
            label="converter",
            node_type=Converter,
            inputs={
                electrical_bus: Flow(nominal_value=self.nominal_power),
                heat_bus_cold: Flow(),
            },
            outputs={heat_bus_warm: Flow()},
            conversion_factors={
                electrical_bus: (1 - ratio) / self.efficiency,
                heat_bus_cold: ratio,
                heat_bus_warm: 1,
            },
        )
