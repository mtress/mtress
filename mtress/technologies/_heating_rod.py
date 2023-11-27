"""This module provides combined heat and power (CHP)"""

import logging
from oemof.solph import Flow
from oemof.solph.components import Converter

from .._abstract_component import AbstractSolphRepresentation
from ..carriers import Electricity, Heat
from ._abstract_technology import AbstractTechnology

LOGGER = logging.getLogger(__file__)


class HeatingRod(AbstractTechnology, AbstractSolphRepresentation):
    """
    Heating Rod represents all electric resistance heat technologies. It converts electricity into heat at a 100% efficiency or COP of 1.      Typically used with other heating technologies such as heat pumps etc. to keep their nominal sizes down and the heating rod helps reach those peak heat demands.
    """

    def __init__(
            self,
            name: str,
            nominal_power: float,
            thermal_temperature: float,
            thermal_efficiency: float = 1,
    ):
        """
        Initialize Heating Rod.

        :param name: Set the name of the component
        :param nominal_power: Nominal heating capacity of the heating rod
        :parma thermal_temperature: Temperature level (°C) of the heat output
                                    from CHP that is recoverable.
        :param thermal_efficiency: Thermal conversion efficiency (LHV) of the CHP
        """
        super().__init__(name=name)

        self.nominal_power = nominal_power
        self.thermal_temperature = thermal_temperature
        self.thermal_efficiency = thermal_efficiency

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        # Add electrical connection
        electricity_carrier = self.location.get_carrier(Electricity)
        electrical_bus = electricity_carrier.distribution

        # Add heat connection
        heat_carrier = self.location.get_carrier(Heat)

        _, temp_level = heat_carrier.get_surrounding_levels(self.thermal_temperature)

        if temp_level not in heat_carrier.levels:
            raise ValueError("No suitable temperature level available")

        heat_bus = heat_carrier.inputs[temp_level]

        self.create_solph_node(
            label="converter",
            node_type=Converter,
            inputs={electrical_bus: Flow()},
            outputs={heat_bus: Flow(nominal_value=self.nominal_power)},
            conversion_factors={heat_bus: self.thermal_efficiency}
        )
