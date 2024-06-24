"""This module provides PEM fuel cell."""

import logging
from dataclasses import dataclass

import numpy as np
from oemof.solph import Flow
from oemof.solph.components import Converter

from .._abstract_component import AbstractSolphRepresentation
from .._helpers._util import enable_templating
from ..carriers import Electricity, GasCarrier, HeatCarrier
from ..physics import HYDROGEN, Gas
from ._abstract_technology import AbstractTechnology

LOGGER = logging.getLogger(__file__)


@dataclass(frozen=True)
class FuelCellTemplate:
    """
    Here we define the different fuel cell technologies (PEM, Alkaline, AEM)
    with their specific parameter values.

    Important references on technologies:
    1. "Hydrogen and fuel cell technologies for heating: A review"
        by Pual E. Dodds et. al.

    2. "Prospects of Fuel Cell Combined Heat and Power Systems"
        by AG. Olabi et. al.

    Users can modify the parameter values for a particular technology type
    if needed or can create user-defined fuel cell technology (e.g., SOFC, PFC,
    MCFC, etc.).
    """

    electrical_efficiency: float
    thermal_efficiency: float
    maximum_temperature: float
    minimum_temperature: float
    gas_input_pressure: float


# Polymer Exchange Membrane Fuel Cell (PEMFC)
PEMFC = FuelCellTemplate(
    electrical_efficiency=0.36,
    thermal_efficiency=0.50,
    maximum_temperature=70,
    minimum_temperature=20,
    gas_input_pressure=80,
)

# Alkaline Fuel Cell (AFC)
AFC = FuelCellTemplate(
    electrical_efficiency=0.37,
    thermal_efficiency=0.45,
    maximum_temperature=65,
    minimum_temperature=20,
    gas_input_pressure=60,
)

#  Anion Exchange Membrane Fuel Cell (AEMFC)
AEMFC = FuelCellTemplate(
    electrical_efficiency=0.33,
    thermal_efficiency=0.42,
    maximum_temperature=55,
    minimum_temperature=20,
    gas_input_pressure=35,
)


class FuelCell(AbstractTechnology, AbstractSolphRepresentation):
    """
    There are various types of fuel cell (FC) technology : PEM, Alkaline, AEM, etc.
    This class module takes PEMFC as default technology, but user can select different
    technology type or can also user-defined FC technology as per the needs.

    Functionality: Fuel cells converts chemical energy (hydrogen) to electricity, and
    potentially produces useful heat and water as byproducts. Fuel Cell could be
    used for various application to produce heat and power with hydrogen as fuel input.
    Hence, it enables better sector coupling between electricity and heating sector.
    They find widespread application in various sectors, especially stationary type fuel
    cell, such as backup power, distributed power generation, and co-generation, in the
    context of the MTRESS energy system.

    PEMFC are usually rated with electrical efficiency (@ LHV) of 35-39% and thermal
    efficiency (@ LHV) of ~ 55%. So, technically overall efficiency of 85-94% could be
    reached, if excess heat could be recovered. However, the behaviour of FC is non-linear
    i.e. electrical  and thermal efficiency varies with load input(H2). The electrical
    efficiency for PEMFC could go as high as 55-60% while thermal efficiency reduces
    simultaneously at part-load operation. To simplify modeling, constant efficiencies
    is assumed, as accounting for the non-linearity would significantly increase
    computational complexity.

    The excess heat could be recovered to increase the overall efficiency of the device.
    Operating temperature of low-temperature FC could range between 50-100 °C, making
    them suitable for space heating and boiling water for residential, commercial building,
    and/or industrial processes, etc. For instance, the H2home project demonstrated the use
    of PEMFC-based combined heat and power (CHP) systems for residential buildings. Ongoing
    research aims to push the operating temperature beyond 100 °C, with high-temperature
    PEMFCs (HT-PEMFCs) even capable of reaching up to 200 °C. Alternatively,
    high-temperature fuel cells like Solid Oxide Fuel Cells (SOFCs) operate at even
    higher temperatures, typically in the range of 500-1000 °C. SOFCs exhibit higher
    electrical efficiency (LHV) of 45-60% and thermal  efficiency (LHV) of 30-45%.
    Despite their advantages, SOFCs are more expensive and have longer cold startup
    times (< 12 hours). They also face challenges in dynamic operation due to the
    high-temperature conditions. But, SOFCs can utilize various fuels, such as natural
    gas, methanol, ethanol, biogas, and coal gas. Fuel Cell CHP uses heat exchanger or
    heat recovery unit to harness heat energy to useful energy. Heat exchangers that
    circulates cooling liquid is used to extract heat for PEMFC, AFC, AEM and cathode
    air flow for SOFC.

    Overall, FC can offer promising solutions to our renewable-based energy system.

    """

    @enable_templating(FuelCellTemplate)
    def __init__(
        self,
        name: str,
        nominal_power: float,
        electrical_efficiency: float,
        thermal_efficiency: float,
        maximum_temperature: float,
        minimum_temperature: float,
        gas_input_pressure: float,
        gas_type: Gas = HYDROGEN,
        inverter_efficiency: float = 0.98,
    ):
        """
        Initialize Fuel Cell (FC)

        :param name: Name of the component
        :param nominal_power: Nominal electrical power output of Fuel Cell (FC)
            (in W)
        :param electrical_efficiency: Electrical efficiency of the Fuel Cell,
            i.e. ratio of electrical output and gas input
        :param thermal_efficiency: Thermal efficiency of the Fuel Cell,
            i.e. ratio of thermal output and gas input
        :param maximum_temperature: Maximum temperature (in °C) at which heat could
            be extracted from FC.
        :param minimum_temperature: Minimum return temperature level (in °C)
        :param gas_input_pressure: Pressure at which gas is injected to FC.
        :param gas_type: Input gas to FC, by default Hydrogen gas is used.
        :param inverter_efficiency: Efficiency for conversion from DC output
            from FC to AC to meet load demands. Default value is 98 %.
        """
        super().__init__(name=name)

        self.nominal_power = nominal_power
        self.electrical_efficiency = electrical_efficiency
        self.thermal_efficiency = thermal_efficiency
        self.maximum_temperature = maximum_temperature
        self.minimum_temperature = minimum_temperature
        self.gas_input_pressure = gas_input_pressure
        self.gas_type = gas_type
        self.inverter_efficiency = inverter_efficiency

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        # Gas connection as an input to Fuel Cell
        gas_carrier = self.location.get_carrier(GasCarrier)

        _, pressure = gas_carrier.get_surrounding_levels(
            self.gas_type, self.gas_input_pressure
        )

        gas_bus = gas_carrier.inputs[self.gas_type][pressure]

        # Convert nominal power capacity of FC in W to nominal gas consumption
        # capacity in kg
        nominal_gas_consumption = self.nominal_power / (
            self.electrical_efficiency * self.gas_type.LHV
        )

        # Electrical connection for FC electrical output
        electricity_carrier = self.location.get_carrier(Electricity)

        # Electrical efficiency with conversion from gas in kg to electricity in W, also
        # includes inverter efficiency.
        electrical_output = (
            self.electrical_efficiency * self.inverter_efficiency * self.gas_type.LHV
        )

        # Heat connection for FC heat output
        heat_carrier = self.location.get_carrier(HeatCarrier)
        heat_bus_warm, heat_bus_cold, ratio = heat_carrier.get_connection_heat_transfer(
            self.maximum_temperature,
            self.minimum_temperature,
        )

        # thermal efficiency with conversion from gas in kg to heat in W.
        heat_output = self.thermal_efficiency * self.gas_type.LHV

        # electricity bus connection
        electricity_bus = electricity_carrier.distribution

        self.create_solph_node(
            label="converter",
            node_type=Converter,
            inputs={
                gas_bus: Flow(nominal_value=nominal_gas_consumption),
                heat_bus_cold: Flow(),
            },
            outputs={
                electricity_carrier.distribution: Flow(),
                heat_bus_warm: Flow(),
            },
            conversion_factors={
                gas_bus: 1,
                heat_bus_cold: self.thermal_efficiency * ratio / (1 - ratio),
                electricity_bus: electrical_output,
                heat_bus_warm: heat_output / (1 - ratio),
            },
        )
