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
        minumum_temperature: float = 0,
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
        self.minumum_temperature = minumum_temperature
        self.efficiency = efficiency

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        # Add electrical connection
        electricity_carrier = self.location.get_carrier(Electricity)
        electrical_bus = electricity_carrier.distribution

        # Add heat connection
        heat_carrier = self.location.get_carrier(HeatCarrier)

        warm_level, _ = heat_carrier.get_surrounding_levels(self.maximum_temperature)
        _, cold_level = heat_carrier.get_surrounding_levels(self.minumum_temperature)

        if cold_level not in heat_carrier.levels:
            raise ValueError(
                f"No suitable temperature level available for {cold_level}."
            )
        if warm_level not in heat_carrier.levels:
            raise ValueError(
                f"No suitable temperature level available for {warm_level}."
            )

        reference_temp = heat_carrier.reference

        heat_bus_warm = heat_carrier.level_nodes[warm_level]
        heat_bus_cold = heat_carrier.level_nodes[cold_level]

        ratio = (cold_level - reference_temp) / (warm_level - reference_temp)

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
