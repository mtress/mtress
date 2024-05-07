"""This module provides ResistiveHeater component (power to heat)"""

import logging
from oemof.solph import Flow
from oemof.solph.components import Converter

from .._abstract_component import AbstractSolphRepresentation
from ..carriers import Electricity, HeatCarrier
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
        efficiency: float = 1,
    ):
        """
        Initialize ResistiveHeater.

        :param name: Set the name of the component.
        :param nominal_power: Nominal heating capacity of the heating rod (in W)
        :parma maximum_temperature: Temperature level (in °C) of the heat output.
        :param efficiency: Thermal conversion efficiency.
        """
        super().__init__(name=name)

        self.nominal_power = nominal_power
        self.maximum_temperature = maximum_temperature
        self.efficiency = efficiency

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        # Add electrical connection
        electricity_carrier = self.location.get_carrier(Electricity)
        electrical_bus = electricity_carrier.distribution

        # Add heat connection
        heat_carrier = self.location.get_carrier(HeatCarrier)

        temp_level, _ = heat_carrier.get_surrounding_levels(self.maximum_temperature)

        if temp_level not in heat_carrier.levels:
            raise ValueError("No suitable temperature level available")

        heat_bus = heat_carrier.level_nodes[temp_level]

        self.create_solph_node(
            label="converter",
            node_type=Converter,
            inputs={electrical_bus: Flow()},
            outputs={heat_bus: Flow(nominal_value=self.nominal_power)},
            conversion_factors={heat_bus: self.efficiency},
        )
