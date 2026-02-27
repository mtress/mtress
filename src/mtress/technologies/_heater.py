"""This module provides simple heater components (X to heat)"""

import logging

from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Converter

from ..carriers import ElectricityCarrier, GasCarrier, HeatCarrier
from ..physics import Gas
from ._abstract_technology import AbstractTechnology

from .._constants import EnergyType

LOGGER = logging.getLogger(__file__)


class AbstractHeater(AbstractTechnology):
    def __init__(
        self,
        name: str,
        maximum_temperature: float,
        minimum_temperature: float,
    ):
        """
        :param name: Set the name of the component.
        :parma maximum_temperature: Temperature (in °C) of the heat output.
        :parma minimum_temperature: Lowest possible temperature (in °C)
            of the inlet.
        """
        super().__init__(name=name)

        self.maximum_temperature = maximum_temperature
        self.minimum_temperature = minimum_temperature

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        self.heat_bus = heat_bus = self.create_solph_node(
            label="heat",
            node_type=Bus,
        )

        # Add heat connection
        heat_carrier = self.location.get_carrier(HeatCarrier)

        in_levels = heat_carrier.get_levels_between(
            self.minimum_temperature, self.maximum_temperature
        )
        out_levels = heat_carrier.get_levels_between(
            in_levels[1], self.maximum_temperature
        )

        for temp_in, temp_out in zip(in_levels, out_levels):
            bus_cold = heat_carrier.level_nodes[temp_in]
            bus_warm = heat_carrier.level_nodes[temp_out]
            self.create_solph_node(
                label=f"heat_{temp_in:.0f}_{temp_out:.0f}",
                node_type=Converter,
                inputs={
                    bus_cold: Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.HEAT,
                        }
                    ),
                    heat_bus: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.HEAT,
                        }
                    ),
                },
                outputs={
                    bus_warm: Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.HEAT,
                        }
                    ),
                },
                conversion_factors={
                    bus_warm: 1,
                    bus_cold: 1,
                    heat_bus: (temp_out - temp_in)
                    * heat_carrier.specific_heat_capacity,
                },
            )


class ResistiveHeater(AbstractHeater):
    """
    ResistiveHeater converts electricity into heat at a given efficiency.
    """

    def __init__(
        self,
        name: str,
        maximum_temperature: float,
        minimum_temperature: float = 0,
        thermal_power_limit: Investment | float = None,
        efficiency: float = 1,
    ):
        """
        Initialize ResistiveHeater.

        :param name: Set the name of the component.
        :param maximum_temperature: Temperature (in °C) of the heat output.
        :param minimum_temperature: Lowest possible temperature (in °C)
            of the inlet.
        :param thermal_power_limit: Nominal heating capacity of the heating rod
            (in W).
        :param efficiency: Thermal conversion efficiency.
        """
        super().__init__(
            name=name,
            maximum_temperature=maximum_temperature,
            minimum_temperature=minimum_temperature,
        )

        self.thermal_power_limit = thermal_power_limit
        self.efficiency = efficiency

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        # Add electrical connection
        electricity_carrier = self.location.get_carrier(ElectricityCarrier)
        electrical_bus = electricity_carrier.distribution

        self.create_solph_node(
            label="heater",
            node_type=Converter,
            inputs={
                electrical_bus: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    }
                )
            },
            outputs={
                self.heat_bus: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    },
                    nominal_value=self.thermal_power_limit,
                )
            },
            conversion_factors={
                electrical_bus: 1,
                self.heat_bus: self.efficiency,
            },
        )


class GasBoiler(AbstractHeater):
    """
    A gas boiler is a closed vessel in which fluid (generally water) is heated.
    """

    def __init__(
        self,
        name: str,
        gas_type: Gas,
        maximum_temperature: float,
        minimum_temperature: float,
        thermal_power_limit: float | Investment,
        efficiency: float,
        input_pressure: float,
    ):
        """
        Initialize Gas Boiler component.

        :param name: Set the name of the component
        :param gas_type: (Gas) type of gas from gas carrier and its share in
                         vol %
        :parma maximum_temperature: Temperature (in °C) of the heat output
        :parma minimum_temperature: Lowest possible temperature (in °C)
            of the inlet.
        :param thermal_power_limit: Nominal heat output capacity (in Watts).
        :param input_pressure: Input pressure of gas or gases (in bar).
        :param efficiency: Thermal conversion efficiency (LHV).

        """
        super().__init__(
            name=name,
            maximum_temperature=maximum_temperature,
            minimum_temperature=minimum_temperature,
        )

        self.gas_type = gas_type
        self.maximum_temperature = maximum_temperature
        self.minimum_temperature = minimum_temperature
        self.thermal_power_limit = thermal_power_limit
        self.input_pressure = input_pressure
        self.efficiency = efficiency

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        gas_carrier = self.location.get_carrier(GasCarrier)
        _, pressure_level = gas_carrier.get_surrounding_levels(
            self.gas_type, self.input_pressure
        )
        gas_bus = gas_carrier.inputs[self.gas_type][pressure_level]

        self.create_solph_node(
            label="converter",
            node_type=Converter,
            inputs={
                gas_bus: Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.GAS,
                    }
                ),
            },
            outputs={
                self.heat_bus: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    },
                    nominal_value=self.thermal_power_limit,
                ),
            },
            conversion_factors={
                self.heat_bus: self.efficiency * self.gas_type.LHV,
            },
        )
