"""This module provides simple heater components (X to heat)"""

from oemof.network.network.nodes import QualifiedLabel
from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Converter

from .._constants import EnergyType
from .._carriers import ElectricityCarrier, GasCarrier, HeatCarrier
from ..physics import Gas
from .._base_mtress_nodes import AbstractTechnology


class AbstractHeater(AbstractTechnology):
    def __init__(
        self,
        label,
        *,
        maximum_temperature: float,
        minimum_temperature: float,
        specific_heat_capacity: float = 1.161,
        location=None,
        custom_properties=None,
    ):
        """
        :param label: Set the label of the component.
        :parma maximum_temperature: Temperature (in °C) of the heat output.
        :parma minimum_temperature: Lowest possible temperature (in °C)
            of the inlet.
        """
        super().__init__(
            label,
            parent_node=location,
            custom_properties=custom_properties,
        )

        self._maximum_temperature = maximum_temperature
        self._minimum_temperature = minimum_temperature
        self._specific_heat_capacity = specific_heat_capacity

        # bookkeeping of heat i/o nodes
        self._temp_nodes = {}

    def _build_core(self):
        self._heat_bus = self.subnode(
            Bus,
            local_name="heat",
        )

        self._out_max_temp = self.subnode(
            Bus,
            local_name=f"output_{self._maximum_temperature}",
            custom_properties={"temperature": self._maximum_temperature},
        )
        self._temp_nodes[self._maximum_temperature] = self._out_max_temp

        self._in_min_temp = self.subnode(
            Bus,
            local_name=f"input_{self._minimum_temperature}",
            custom_properties={"temperature": self._minimum_temperature},
        )
        self._temp_nodes[self._minimum_temperature] = self._in_min_temp

        self.inbound_interfaces[EnergyType.HEAT] = [self._in_min_temp]
        self.outbound_interfaces[EnergyType.HEAT] = [self._out_max_temp]

    def get_temp_node(self, temp: float) -> Bus:
        node = self._temp_nodes.get(temp)
        if node is not None:
            return node
        else:
            node = self.subnode(
                Bus,
                local_name=f"i/o_{temp}",
                custom_properties={"temperature": temp},
            )
            self._temp_nodes[temp] = node
            return node


class ResistiveHeater(AbstractHeater):
    """
    ResistiveHeater converts electricity into heat at a given efficiency.
    """

    def __init__(
        self,
        label,
        *,
        maximum_temperature: float,
        minimum_temperature: float = 0,
        thermal_power_limit: Investment | float = None,
        efficiency: float = 1,
        location=None,
        custom_properties=None,
    ):
        """
        Initialize ResistiveHeater.

        :param label: Set the label of the component.
        :param maximum_temperature: Temperature (in °C) of the heat output.
        :param minimum_temperature: Lowest possible temperature (in °C)
            of the inlet.
        :param thermal_power_limit: Nominal heating capacity of the heating rod
            (in W).
        :param efficiency: Thermal conversion efficiency.
        """
        super().__init__(
            label,
            maximum_temperature=maximum_temperature,
            minimum_temperature=minimum_temperature,
            location=location,
            custom_properties=custom_properties,
        )

        self.thermal_power_limit = thermal_power_limit
        self.efficiency = efficiency

        self._build_core()

    def _build_core(self):
        super()._build_core()

        # add technology specific inlet
        self._in_electricity = self.subnode(
            Bus,
            local_name="input_electricity",
        )
        self.inbound_interfaces[EnergyType.ELECTRICITY] = [
            self._in_electricity
        ]

        # technology specific converter
        self.subnode(
            Converter,
            local_name="heater",
            inputs={
                self._in_electricity: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    }
                )
            },
            outputs={
                self._heat_bus: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    },
                    nominal_value=self.thermal_power_limit,
                )
            },
            conversion_factors={
                self._in_electricity: 1,
                self._heat_bus: self.efficiency,
            },
        )

    def establish_interconnections(self):
        if self.parent:
            # get carriers
            heat_carrier: HeatCarrier = self.parent.get_carrier(HeatCarrier)
            electricity_carrier: ElectricityCarrier = self.parent.get_carrier(
                ElectricityCarrier
            )

            # connect electricity
            self._in_electricity.inputs[electricity_carrier.distribution] = (
                Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    }
                )
            )

            if self._maximum_temperature not in heat_carrier.levels:
                raise ValueError(
                    "Maximum temperature must be a temperature level"
                )
            if (
                self._specific_heat_capacity
                != heat_carrier.specific_heat_capacity
            ):
                raise ValueError("Specific heat capacities need to match")

            # get heat levels
            in_levels = heat_carrier.get_levels_between(
                self._minimum_temperature, self._maximum_temperature
            )
            out_levels = heat_carrier.get_levels_between(
                in_levels[1], self._maximum_temperature
            )

            for temp_in, temp_out in zip(in_levels, out_levels):
                hc_bus_cold = heat_carrier.level_nodes[temp_in]
                hc_bus_warm = heat_carrier.level_nodes[temp_out]
                bus_in = self.get_temp_node(temp_in)
                bus_out = self.get_temp_node(temp_out)

                # connect busses
                bus_in.inputs[hc_bus_cold] = Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.HEAT,
                    }
                )
                bus_out.outputs[hc_bus_warm] = Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.HEAT,
                    }
                )

                # converter
                self.subnode(
                    Converter,
                    local_name=f"heat_{temp_in:.0f}_{temp_out:.0f}",
                    inputs={
                        bus_in: Flow(
                            custom_properties={
                                "unit": "kg/h",
                                "energy_type": EnergyType.HEAT,
                            }
                        ),
                        self._heat_bus: Flow(
                            custom_properties={
                                "unit": "W",
                                "energy_type": EnergyType.HEAT,
                            }
                        ),
                    },
                    outputs={
                        bus_out: Flow(
                            custom_properties={
                                "unit": "kg/h",
                                "energy_type": EnergyType.HEAT,
                            }
                        ),
                    },
                    conversion_factors={
                        bus_out: 1,
                        bus_in: 1,
                        self._heat_bus: (temp_out - temp_in)
                        * self._specific_heat_capacity,
                    },
                )

        else:
            # min to max converter
            self.subnode(
                Converter,
                local_name=f"heat_{self._minimum_temperature:.0f}_{self._maximum_temperature:.0f}",
                inputs={
                    self._in_min_temp: Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.HEAT,
                        }
                    ),
                    self._heat_bus: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.HEAT,
                        }
                    ),
                },
                outputs={
                    self._out_max_temp: Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.HEAT,
                        }
                    ),
                },
                conversion_factors={
                    self._out_max_temp: 1,
                    self._in_min_temp: 1,
                    self._heat_bus: (
                        self._maximum_temperature - self._minimum_temperature
                    )
                    * self._specific_heat_capacity,
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
        super()._build_core()

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
