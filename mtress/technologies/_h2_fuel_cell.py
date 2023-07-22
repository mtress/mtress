"""This module provides PEM fuel cell."""

import logging

import numpy as np
from oemof.solph import Flow
from oemof.solph.components import Transformer

from .._abstract_component import AbstractSolphComponent
from ..carriers import Electricity, Heat, Hydrogen
from ..physics import H2_LHV
from ._abstract_technology import AbstractTechnology

LOGGER = logging.getLogger(__file__)


class PEMFuelCell(AbstractTechnology, AbstractSolphComponent):
    """
    Polymer Exchange Membrane Fuel Cell (PEMFC)

    Functionality: Fuel cells converts chemical energy (hydrogen) to electricity, and potentially produces useful heat
    and water as byproducts. PEM Fuel Cell could be used for various application to produce heat and power with hydrogen
    as fuel input. Hence, it enables better sector coupling between electricity and heating sector. They find widespread
    application in various sectors, especially stationary type fuel cell such as backup power, distributed power
    generation, and co-generation, in the context of the MTRESS energy system.

    PEMFC are usually rated with electrical efficiency (@ LHV) of 35-39% and thermal efficiency (@ LHV) of
    ~ 55%. So, technically overall efficiency of 85-94% could be reached, if excess could be recovered. However, the
    behaviour of FC is non-linear i.e. electrical  and thermal efficiency varies with load input(H2).
    The electrical efficiency for PEMFC could go as high as 55-60% while thermal efficiency reduces simultaneously at
    part-load operation. To simplify modeling, constant efficiencies is assumed, as accounting for the non-linearity
    would significantly increase computational complexity.

    The excess heat could be recovered to increase the overall efficiency of the device. Operating temperature of PEMFC
    could range between 50-100 °C, making them suitable for space heating and boiling water for residential, commercial
    building, and/or industrial processes, etc. For instance, the H2home project demonstrated the use of PEMFC-based
    combined heat and power (CHP) systems for residential buildings. Ongoing research aims to push the operating
    temperature beyond 100 °C, with high-temperature PEMFCs (HT-PEMFCs) even capable of reaching up to 200 °C.
    Alternatively, high-temperature fuel cells like Solid Oxide Fuel Cells (SOFCs) operate at even higher temperatures,
    typically in the range of 500-1000 °C. SOFCs exhibit higher electrical efficiency (LHV) of 45-60% and thermal
    efficiency (LHV) of 30-45%. Despite their advantages, SOFCs are more expensive and have longer cold startup times
    (< 12 hours). They also face challenges in dynamic operation due to the high-temperature conditions. But, SOFCs can
    utilize various fuels, such as natural gas, methanol, ethanol, biogas, and coal gas.Fuel Cell CHP uses heat
    exchanger or heat recovery unit to harness heat energy to useful energy. Heat exchangers that circulates cooling
    liquid is used to extract heat for PEMFC and cathode air flow for SOFC.

    Overall, fuel Cell could offer promising solutions to our energy system.

    """

    def __init__(
        self,
        name: str,
        nominal_power: float,
        electrical_efficiency: float = 0.36,
        inverter_efficiency: float = 0.95,
        thermal_efficiency: float = 0.50,
        waste_heat_temperature: float = 70.0,
        hydrogen_input_pressure: float = 1.0,
    ):
        """
        Initialize Fuel Cell.

        :param name: Name of the component
        :param nominal_power: Nominal electrical power output capacity of PEMFC
        :param electrical_efficiency: Electrical efficiency of the PEMFC,
            i.e. ratio of heat output and electrical input
        :param inverter_efficiency: Efficiency for conversion from DC to AC to meet AC load demands.
        :param thermal_efficiency: Thermal efficiency of the Fuel Cell,
            i.e. ratio of thermal output and electrical input
        :param waste_heat_temperature: Temperature at which heat could be extracted from FC.
        :param hydrogen_input_pressure: Pressure at which hydrogen is injected to FC.
        :param minimal_power: Minimal power relative to nominal power, defaults to 0.2
        """
        super().__init__(name=name)

        self.nominal_power = nominal_power
        self.electrical_efficiency = electrical_efficiency
        self.thermal_efficiency = thermal_efficiency
        self.inverter_efficiency = inverter_efficiency
        self.waste_heat_temperature = waste_heat_temperature
        self.hydrogen_input_pressure = hydrogen_input_pressure

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        # Hydrogen connection as an input to Fuel Cell
        h2_carrier = self.location.get_carrier(Hydrogen)

        pressure, _ = h2_carrier.get_surrounding_levels(self.hydrogen_input_pressure)

        if np.isinf(pressure):
            raise ValueError("No suitable pressure level available")

        h2_bus = h2_carrier.inputs[pressure]

        # Convert Nominal Power Capacity of Fuel Cell (kW) to Nominal H2 Consumption Capacity (kg)
        nominal_h2_consumption = self.nominal_power / (
            self.electrical_efficiency * H2_LHV
        )

        # Hydrogen and fuel cell technologies for heating: A review by Pual E. Dodds et. al.
        # suggest that the PEMFC electrical efficiency ranges from 35 - 39% and thermal efficiency at 55% based on LHV
        # as a rated specification when it is new, which are slightly higher than in practical scenario, that's why the
        # lower end electrical and thermal efficiency is considered for this implementation.

        # Electrical connection for FC electrical output
        electricity_carrier = self.location.get_carrier(Electricity)
        electrical_bus = electricity_carrier.production

        # Electrical efficiency with conversion from H2 kg to KW electricity, also includes inverter efficiency.
        electrical_output = (
            self.electrical_efficiency * self.inverter_efficiency * H2_LHV
        )

        # Heat connection for FC heat output
        heat_carrier = self.location.get_carrier(Heat)

        # PEM Fuel cell generates waste heat at around 60-80 °C, considered 70 °C in this implementation.
        # "Prospects of Fuel Cell Combined Heat and Power Systems" by AG. Olabi et. al.

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
        heat_output = self.thermal_efficiency * H2_LHV
        heat_bus = heat_carrier.inputs[temp_level]

        self.create_solph_component(
            label="transformer",
            component=Transformer,
            inputs={h2_bus: Flow(nominal_value=nominal_h2_consumption)},
            outputs={
                electrical_bus: Flow(),
                heat_bus: Flow(),
            },
            conversion_factors={
                h2_bus: 1,
                electrical_bus: electrical_output,
                heat_bus: heat_output,
            },
        )
