"""This module provides combined heat and power (CHP)"""

import logging
import numpy as np
from oemof.solph import Flow
from oemof.solph.components import Converter

from .._abstract_component import AbstractSolphRepresentation
from ..carriers import Electricity, Heat, GasCarrier, Gas
from ._abstract_technology import AbstractTechnology

LOGGER = logging.getLogger(__file__)


class CHP(AbstractTechnology, AbstractSolphRepresentation):
    """
    Combined heat and power (CHP) technology can take in bio-methane or biogas
    from Anaerobic Digestion (AD) plant for example or natural gas via local gas
    grid. CHP generates electricity and heat as an output.

    Note: This CHP does not take gas mixtures.
    """

    def __init__(
        self,
        name: str,
        gas_type: Gas,
        thermal_temperature: float,
        nominal_power: float = None,
        input_pressure: float = 15,
        electric_efficiency: float = 0.32,
        thermal_efficiency: float = 0.43,
    ):
        """
        Initialize CHP component.

        :param name: Set the name of the component
        :param gas_type: Type of gas from gas carrier
        :parma thermal_temperature: Temperature level (°C) of the heat output
                                    from CHP that is recoverable.
        :param nominal_power: Nominal electric output capacity of the CHP
        :param input_pressure: gas input input_pressure for CHP, default to 15
        :param electric_efficiency: Electric conversion efficiency (LHV) of the CHP
        :param thermal_efficiency: Thermal conversion efficiency (LHV) of the CHP

        """
        super().__init__(name=name)

        self.gas_type = gas_type
        self.thermal_temperature = thermal_temperature
        self.nominal_power = nominal_power
        self.input_pressure = input_pressure
        self.electric_efficiency = electric_efficiency
        self.thermal_efficiency = thermal_efficiency

        # Solph specific parameters
        self.electricity_bus = None
        self.heat_bus = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        # Add natural gas carrier for import
        gas_carrier = self.location.get_carrier(GasCarrier)
        surrounding_levels = gas_carrier.get_surrounding_levels(self.input_pressure)
        _, pressure = surrounding_levels[self.gas_type]

        if pressure not in gas_carrier.pressures[self.gas_type]:
            raise ValueError("Pressure must be a valid input_pressure level")

        gas_bus = gas_carrier.distribution[self.gas_type][pressure]

        # Convert Nominal Power Capacity of Fuel Cell (kW) to Nominal NG Consumption
        # Capacity (kg)
        nominal_gas_consumption = self.nominal_power / (
            self.electric_efficiency * self.gas_type.LHV
        )

        # Add heat connection
        heat_carrier = self.location.get_carrier(Heat)
        heat_output = self.thermal_efficiency * self.gas_type.LHV

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
        # Electrical efficiency with conversion from NG kg to KWh electricity
        electrical_output = self.electric_efficiency * self.gas_type.LHV

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
                electrical_bus: electrical_output,
                heat_bus: heat_output,
            },
        )


