"""This module provides PEM fuel cell."""

import logging

import numpy as np
from oemof.solph import Flow
from oemof.solph.components import Converter
from dataclasses import dataclass
from typing import Optional
from .._abstract_component import AbstractSolphRepresentation
from ..carriers import Electricity, Heat, GasCarrier
from ..physics import HYDROGEN
from ._abstract_technology import AbstractTechnology

LOGGER = logging.getLogger(__file__)


@dataclass(frozen=True)
class Fuel_Cell_Template:
    """
    Here we define the different fuel cell technologies (PEM, Alkaline, AEM)
    with their specific parameter values.

    "Hydrogen and fuel cell technologies for heating: A review"
    by Pual E. Dodds et. al. suggest that the PEMFC electrical efficiency ranges
    from 35 - 39% and thermal efficiency at 55% based on LHV as a rated
    specification when it is new, which are slightly higher than in practical
    scenario. PEM Fuel cell generates waste heat at around 60-80 °C, considered
    70 °C in this implementation. "Prospects of Fuel Cell Combined Heat and Power
    Systems" by AG. Olabi et. al.

    Users can modify the parameter values for a particular technology type
    if needed or can create user-defined fuel cell technology (e.g., SOFC, PFC,
    MCFC, etc.).
    """
    electrical_efficiency: float
    thermal_efficiency: float
    waste_heat_temperature: float
    hydrogen_input_pressure: float


# Polymer Exchange Membrane Fuel Cell (PEMFC)
PEMFC = Fuel_Cell_Template(
    electrical_efficiency=0.36,
    thermal_efficiency=0.50,
    waste_heat_temperature=70,
    hydrogen_input_pressure=80,
)

# Alkaline Fuel Cell (AFC)
AFC = Fuel_Cell_Template(
    electrical_efficiency=0.37,
    thermal_efficiency=0.45,
    waste_heat_temperature=65,
    hydrogen_input_pressure=60,
)

#  Anion Exchange Membrane Fuel Cell (AEMFC)
AEMFC = Fuel_Cell_Template(
    electrical_efficiency=0.33,
    thermal_efficiency=0.42,
    waste_heat_temperature=55,
    hydrogen_input_pressure=35,
)


class FuelCell(AbstractTechnology, AbstractSolphRepresentation):
    """
    There are various types of fuel cell (FC) technology : PEM, Alkaline, AEM, etc.
    This class module takes PEMFC as default technology, but user can select different
    technology type or can also user-defined their own FC technology as per the needs.

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

    def __init__(
            self,
            name: str,
            nominal_power: float,
            electrical_efficiency: Optional[float] = None,
            inverter_efficiency: float = 0.98,
            thermal_efficiency: Optional[float] = None,
            waste_heat_temperature: Optional[float] = None,
            hydrogen_input_pressure: Optional[float] = None,
            fuel_cell_type: Optional[Fuel_Cell_Template] = PEMFC,
    ):
        """
        Initialize Fuel Cell (FC)

        :param name: Name of the component
        :param nominal_power: Nominal electrical power output capacity of Fuel Cell (FC)
        :param electrical_efficiency: Electrical efficiency of the Fuel Cell,
            i.e. ratio of electrical output and hydrogen gas input
        :param inverter_efficiency: Efficiency for conversion from DC output from FC to
            AC to meet load demands. Default value is 98 %
        :param thermal_efficiency: Thermal efficiency of the Fuel Cell,
            i.e. ratio of thermal output and hydrogen gas input
        :param waste_heat_temperature: Temperature (°C) at which heat could be extracted
            from FC.
        :param hydrogen_input_pressure: Pressure at which hydrogen is injected to FC.
        """
        super().__init__(name=name)

        self.nominal_power = nominal_power
        self.electrical_efficiency = electrical_efficiency or \
                                     fuel_cell_type.electrical_efficiency
        self.thermal_efficiency = thermal_efficiency or \
                                  fuel_cell_type.thermal_efficiency
        self.inverter_efficiency = inverter_efficiency
        self.waste_heat_temperature = waste_heat_temperature or \
                                      fuel_cell_type.waste_heat_temperature
        self.hydrogen_input_pressure = hydrogen_input_pressure or \
                                       fuel_cell_type.hydrogen_input_pressure

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        # Hydrogen connection as an input to Fuel Cell
        gas_carrier = self.location.get_carrier(GasCarrier)

        _, pressure = gas_carrier.get_surrounding_levels(HYDROGEN, self.hydrogen_input_pressure)

        h2_bus = gas_carrier.inputs[HYDROGEN][pressure]

        # Convert Nominal Power Capacity of Fuel Cell in kW to Nominal H2 Consumption
        # Capacity in kg
        nominal_h2_consumption = self.nominal_power / (
                self.electrical_efficiency * HYDROGEN.LHV
        )

        # Electrical connection for FC electrical output
        electricity_carrier = self.location.get_carrier(Electricity)

        # Electrical efficiency with conversion from H2 kg to KW electricity, also
        # includes inverter efficiency.
        electrical_output = (
                self.electrical_efficiency * self.inverter_efficiency * HYDROGEN.LHV
        )

        # Heat connection for FC heat output
        heat_carrier = self.location.get_carrier(Heat)

        temp_level, _ = heat_carrier.get_surrounding_levels(self.waste_heat_temperature)

        if np.isinf(temp_level):
            ValueError(
                "No suitable temperature level available for fuel cell temperature"
            )

        if self.waste_heat_temperature - temp_level > 15:
            LOGGER.info(
                "Waste heat temperature from fuel cell is significantly"
                "higher than suitable temperature level"
            )

        # thermal efficiency with conversion from H2 kg to KW heat.
        heat_output = self.thermal_efficiency * HYDROGEN.LHV
        heat_bus = heat_carrier.inputs[temp_level]

        self.create_solph_node(
            label="converter",
            node_type=Converter,
            inputs={h2_bus: Flow(nominal_value=nominal_h2_consumption)},
            outputs={
                electricity_carrier.distribution: Flow(),
                heat_bus: Flow(),
            },
            conversion_factors={
                h2_bus: 1,
                electricity_carrier.distribution: electrical_output,
                heat_bus: heat_output,
            },
        )
