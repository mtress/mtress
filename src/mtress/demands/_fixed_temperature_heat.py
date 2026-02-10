"""Room heating technologies."""

from oemof.solph import Bus, Flow
from oemof.solph.components import Converter, Sink, Source

from .._data_handler import TimeseriesType, TimeseriesSpecifier
from ..carriers import HeatCarrier
from ._abstract_demand import AbstractDemand

from .._constants import EnergyType


class AbstractFixedTemperature(AbstractDemand):
    """
    Superclass for heating or coolig with a fixed return temperature.

    Takes energy from the flow temperature level and returns energy at the
    return temperature level.

    Functionality: Demands contain time series of energy that is needed.
        The heat demand automatically connects to its corresponding
        heat  carrier. A name identifying the demand has to be given that
        is unique for the location, because multiple demands of one type
        can exist for one location.

    Procedure: Create a simple heat demand by doing the following:

            house_1.add(demands.FixedTemperatureHeat(
                flow_temperature=30, # in °C
                return_temperature=20, # in °C
                time_series=[50]))

    Notice: While energy from electricity and the gaseous carriers is
     just consumed, heat demands have a returning energy flow.
    """

    def __init__(
        self,
        label,
        *,
        flow_temperature: float,
        return_temperature: float,
        time_series: TimeseriesSpecifier,
        specific_heat_capacity: float = 1.161,
        location=None,
        custom_properties=None,
    ):
        """
        Initialize space heater.

        :param flow_temperature: Flow temperature
        :param return_temperature: Return temperature
        """
        super().__init__(
            label,
            location=location,
            custom_properties=custom_properties,
        )

        self.flow_temperature = flow_temperature
        self.return_temperature = return_temperature
        self.specific_heat_capacity = specific_heat_capacity

        self._time_series = time_series


class FixedTemperatureHeating(AbstractFixedTemperature):
    def __init__(
        self,
        label,
        *,
        min_flow_temperature: float,
        return_temperature: float,
        time_series: TimeseriesSpecifier,
        specific_heat_capacity: float = 1.161,
        location=None,
        custom_properties=None,
    ):
        """
        Heating demand with a fixed return temperature.

        :param min_flow_temperature: minimum temperature
            that can be used for heating
        :param return_temperature: return temperature
        :param time_series: demand time series (in W)
        """
        super().__init__(
            label,
            flow_temperature=None,
            return_temperature=return_temperature,
            time_series=time_series,
            specific_heat_capacity=specific_heat_capacity,
            location=location,
            custom_properties=custom_properties,
        )

        if not min_flow_temperature > return_temperature:
            raise ValueError("Flow must be higher than return temperature")

        self.min_flow_temperature = min_flow_temperature

        self._build_core()

    def _build_core(self):
        self._input_node = self.subnode(
            Bus,
            local_name="input",
        )
        self._output_node = self.subnode(
            Bus,
            local_name="output",
            custom_properties={"temperature": self.return_temperature},
        )

        self._sink = self.subnode(
            Sink,
            local_name="sink",
            inputs={},
        )

        self.inbound_interfaces[EnergyType.HEAT] = [self._input_node]
        self.outbound_interfaces[EnergyType.HEAT] = [self._output_node]

    def establish_interconnections(self):
        if self.parent:
            heat_carrier: HeatCarrier = self.parent.get_carrier(HeatCarrier)

            # TODO: register temp levels @ HeatCarrier
            if self.return_temperature not in heat_carrier.levels:
                raise ValueError(
                    "Return temperature must be a temperature level"
                )
            if (
                self.specific_heat_capacity
                != heat_carrier.specific_heat_capacity
            ):
                raise ValueError("Specific heat capacities need to match")

            # get max temp availabe for heating
            maximum_t, _ = heat_carrier.get_surrounding_levels(
                self.min_flow_temperature
            )

            # connect interface nodes to heat carrier
            self._input_node.inputs[heat_carrier.level_nodes[maximum_t]] = (
                Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.HEAT,
                    }
                )
            )
            self._output_node.outputs[
                heat_carrier.level_nodes[self.return_temperature]
            ] = Flow(
                custom_properties={
                    "unit": "kg/h",
                    "energy_type": EnergyType.HEAT,
                }
            )

            # create converter and connect to sink and interface nodes
            inputs = {}
            outputs = {}
            conversion_factors = {}

            inputs[self._input_node] = Flow(
                custom_properties={
                    "unit": "W",
                    "energy_type": EnergyType.HEAT,
                }
            )

            outputs[self._output_node] = Flow(
                custom_properties={
                    "unit": "W",
                    "energy_type": EnergyType.HEAT,
                }
            )

            outputs[self._sink] = Flow(
                custom_properties={
                    "unit": "W",
                    "energy_type": EnergyType.HEAT,
                },
                nominal_value=1,
                fix=self._time_series,
            )

            conversion_factors = {
                self._input_node: 1,
                self._output_node: 1,
                self._sink: (self.flow_temperature - self.return_temperature)
                * heat_carrier.specific_heat_capacity,
            }

            self.subnode(
                Converter,
                local_name="heat_exchanger",
                inputs=inputs,
                outputs=outputs,
                conversion_factors=conversion_factors,
            )


class FixedTemperatureCooling(AbstractFixedTemperature):
    def __init__(
        self,
        label,
        *,
        max_flow_temperature: float,
        return_temperature: float,
        time_series,
        specific_heat_capacity: float = 1.161,
        location=None,
        custom_properties=None,
    ):
        """
        Cooling demand with a fixed return temperature.

        :param max_flow_temperature: maximum temperature
            that can be used for cooling
        :param return_temperature: return temperature
        :param time_series: demand time series (in W)
        """
        super().__init__(
            label,
            flow_temperature=None,
            return_temperature=return_temperature,
            time_series=time_series,
            specific_heat_capacity=specific_heat_capacity,
            location=location,
            custom_properties=custom_properties,
        )

        if not max_flow_temperature < return_temperature:
            raise ValueError("Flow must be lower than return temperature")

        self.max_flow_temperature = max_flow_temperature

        self._build_core()

    def _build_core(self):
        self._input_node = self.subnode(
            Bus,
            local_name="input",
        )
        self._output_node = self.subnode(
            Bus,
            local_name="output",
            custom_properties={"temperature": self.return_temperature},
        )

        self._source = self.subnode(
            Source,
            local_name="source",
            outputs={},
        )

        self.inbound_interfaces[EnergyType.HEAT] = [self._input_node]
        self.outbound_interfaces[EnergyType.HEAT] = [self._output_node]

    def establish_interconnections(self):
        if self.parent:
            heat_carrier: HeatCarrier = self.parent.get_carrier(HeatCarrier)

            # TODO: register temp levels @ HeatCarrier
            if self.return_temperature not in heat_carrier.levels:
                raise ValueError(
                    "Return temperature must be a temperature level"
                )
            if (
                self.specific_heat_capacity
                != heat_carrier.specific_heat_capacity
            ):
                raise ValueError("Specific heat capacities need to match")

            # get min temp availabe for cooling
            _, minimum_t = heat_carrier.get_surrounding_levels(
                self.max_flow_temperature
            )

            # connect interface nodes to heat carrier
            self._input_node.inputs[heat_carrier.level_nodes[minimum_t]] = (
                Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.HEAT,
                    }
                )
            )
            self._output_node.outputs[
                heat_carrier.level_nodes[self.return_temperature]
            ] = Flow(
                custom_properties={
                    "unit": "kg/h",
                    "energy_type": EnergyType.HEAT,
                }
            )

            # create converter and connect to source and interface nodes
            inputs = {}
            outputs = {}
            conversion_factors = {}

            inputs[self._input_node] = Flow(
                custom_properties={
                    "unit": "W",
                    "energy_type": EnergyType.HEAT,
                }
            )

            inputs[self._source] = Flow(
                custom_properties={
                    "unit": "W",
                    "energy_type": EnergyType.HEAT,
                },
                nominal_value=1,
                fix=self._time_series,
            )

            outputs[self._output_node] = Flow(
                custom_properties={
                    "unit": "W",
                    "energy_type": EnergyType.HEAT,
                }
            )

            conversion_factors = {
                self._input_node: 1,
                self._source: heat_carrier.specific_heat_capacity
                * (self.return_temperature - minimum_t),
                self._output_node: 1,
            }

            self.subnode(
                Converter,
                local_name="heat_exchanger",
                inputs=inputs,
                outputs=outputs,
                conversion_factors=conversion_factors,
            )
