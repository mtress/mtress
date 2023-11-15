"""This module provides hydrogen electrolyser."""


import logging

import numpy as np
from oemof.solph import Flow
from oemof.solph.components import Converter

from .._abstract_component import AbstractSolphRepresentation
from ..carriers import Electricity, Heat, GasCarrier
from ..physics import HYDROGEN
from ._abstract_technology import AbstractTechnology

LOGGER = logging.getLogger(__file__)


class Electrolyser(AbstractTechnology, AbstractSolphRepresentation):
    """
    Electrolyser split water into hydrogen and oxygen with the electricity as input
    source of energy. Hydrogen can be used as an energy carrier for various applications.
    Excess heat from electrolyser can also be utilised. Oxygen produced in the electrolysis
    process is not considered in MTRESS.
    There are various types of electrolyser : PEM, Alkaline, AEM, SOEC, etc. This class
    module takes PEM electrolyser as default technology, but user can change the default
    parameter values to consider other electrolyser types.
    """

    def __init__(
        self,
        name: str,
        nominal_power: float,
        hydrogen_efficiency: float = 0.7,
        thermal_efficiency: float = 0.2,
        waste_heat_temperature: float = 75.0,
        hydrogen_output_pressure: float = 30.0,
        minimal_power: float = 0.2,
    ):
        """
        Initialize PEM electrolyser.

        :param name: Name of the Component
        :param nominal_power: Nominal electrical power of the component
        :param hydrogen_efficiency: Electrical efficiency of the electrolyser,
            i.e. ratio of heat output and electrical input
        :param thermal_efficiency: Thermal efficiency of the electrolyser,
            i.e. ratio of thermal output and electrical input
        :param minimal_power: Minimal power relative to nominal power, defaults to 0.2
        """
        super().__init__(name=name)

        self.nominal_power = nominal_power
        self.hydrogen_efficiency = hydrogen_efficiency
        self.thermal_efficiency = thermal_efficiency
        self.waste_heat_temperature = waste_heat_temperature
        self.hydrogen_output_pressure = hydrogen_output_pressure
        self.minimal_power = minimal_power

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        # Electrical connection
        electricity_carrier = self.location.get_carrier(Electricity)
        electrical_bus = electricity_carrier.distribution

        # Hydrogen connection
        gas_carrier = self.location.get_carrier(GasCarrier)

        # PEM electrolyser produce hydrogen at an input_pressure of around 30 bar or above,
        # see e.g.
        # https://en.wikipedia.org/wiki/Polymer_electrolyte_membrane_electrolysis
        # or https://www.h-tec.com/produkte/detail/h-tec-pem-elektrolyseur-me450/me450/

        pressure, _ = gas_carrier.get_surrounding_levels(HYDROGEN, self.hydrogen_output_pressure)

        h2_bus = gas_carrier.inputs[HYDROGEN][pressure]

        # H2 output in kg
        h2_output = self.hydrogen_efficiency / HYDROGEN.HHV

        # Heat connection
        heat_carrier = self.location.get_carrier(Heat)

        # PEM electrolyser produce waste heat at around 77 °C
        # see e.g. Heat Management of PEM Electrolysis. A study on the potential of
        # excess heat from medium­ to large­scale PEM electrolysis and the performance
        # analysis of a dedicated cooling system by W.J. Tiktak
        temp_level, _ = heat_carrier.get_surrounding_levels(self.waste_heat_temperature)
        if np.isinf(temp_level):
            ValueError("No suitable temperature level available")

        if self.waste_heat_temperature - temp_level > 15:
            LOGGER.info(
                "Waste heat temperature significantly"
                "higher than suitable temperature level"
            )

        heat_bus = heat_carrier.inputs[temp_level]

        # TODO: Minimal power implementieren
        self.create_solph_node(
            label="converter",
            node_type=Converter,
            inputs={electrical_bus: Flow(nominal_value=self.nominal_power)},
            outputs={
                h2_bus: Flow(),
                heat_bus: Flow(),
            },
            conversion_factors={
                electrical_bus: 1,
                h2_bus: h2_output,
                heat_bus: self.thermal_efficiency,
            },
        )
