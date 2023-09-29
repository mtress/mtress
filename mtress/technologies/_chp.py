"""This module provides combined heat and power (CHP)"""

import logging
import numpy as np
from oemof.solph import Flow
from oemof.solph.components import Converter

from .._abstract_component import AbstractSolphRepresentation
from ..carriers import Electricity, Heat, Gas
from ._abstract_technology import AbstractTechnology

LOGGER = logging.getLogger(__file__)


class CHP(AbstractTechnology, AbstractSolphRepresentation):
    """
    Combined heat and power (CHP) technology can take in bio-methane or biogas
    from Anaerobic Digestion (AD) plant for example or natural gas via local gas
    grid. CHP generates electricity and heat as an output.
    """

    def __init__(
            self,
            name: str,
            nominal_power: float = None,
            pressure: float = 15,
            electric_efficiency: float = 0.32,
            thermal_efficiency: float = 0.43,
            thermal_temperature: float = 500,
    ):
        """
        Initialize CHP component.

        :param name: Set the name of the component
        :param nominal_power: Nominal electric output capacity of the CHP
        :param electric_efficiency: Electric conversion efficiency of the CHP
        :param thermal_efficiency: Thermal conversion efficiency of the CHP
        :parma thermal_temperature: Temperature level (°C) of the heat output
                                    from CHP that is recoverable.
        """
        super().__init__(name=name)

        self.nominal_power = nominal_power
        self.pressure = pressure
        self.electric_efficiency = electric_efficiency
        self.thermal_efficiency = thermal_efficiency
        self.thermal_temperature = thermal_temperature

        # Solph specific parameters
        self.electricity_bus = None
        self.heat_bus = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        # Add natural gas carrier for import
        gas_carrier = self.location.get_carrier(Gas)
        gas_bus = gas_carrier.distribution[self.pressure]

        nominal_gas_consumption = self.nominal_power / self.electric_efficiency

        # Add heat connection
        heat_carrier = self.location.get_carrier(Heat)
        th_efficiency = self.thermal_efficiency

        temp_level, _ = heat_carrier.get_surrounding_levels(self.thermal_temperature)

        if np.isinf(temp_level):
            ValueError("No suitable temperature level available")

        if self.thermal_temperature - temp_level > 15:
            LOGGER.info(
                "Waste heat temperature from CHP is significantly"
                "higher than suitable temperature level"
            )

        heat_bus = heat_carrier.inputs[temp_level]

        # Add electrical connection
        electricity_carrier = self.location.get_carrier(Electricity)
        electrical_bus = electricity_carrier.distribution
        el_efficiency = self.electric_efficiency

        self.create_solph_node(
            label="converter",
            node_type=Converter,
            inputs={gas_bus: Flow(nominal_value=nominal_gas_consumption)},
            outputs={
                electrical_bus: Flow(),
                heat_bus: Flow(),
            },
            conversion_factors={
                gas_bus: 1,
                electrical_bus: el_efficiency,
                heat_bus: th_efficiency,
            }
        )


