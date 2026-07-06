"""Room heating technologies."""

from abc import abstractmethod
from collections import deque

from oemof.solph import Bus, Flow
from oemof.solph._plumbing import _FakeSequence
from oemof.solph._plumbing import sequence
from oemof.solph.components import Converter, Sink, Source

from .._energy_types import EnergyFlowHeat
from .._energy_types import EnergyQuality
from .._energy_types import EnergyType
from .._energy_types import MassFlowHeat
from .._energy_types import TemperatureBus
from .._data_handler import TimeseriesSpecifier
from ..carriers import HeatCarrier
from .._base_mtress_nodes import AbstractTechnology


class AbstractHeatExchanger(AbstractTechnology):

    def __init__(
        self,
        label,
        *,
        reference_input,
        reference_output,
        reservoir_flow: EnergyFlowHeat,
        specific_heat_capacity,
        parent_node=None,
        custom_properties=None,
    ):
        super().__init__(
            label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        self.specific_heat_capacity = specific_heat_capacity

        self._reservoir_flow = reservoir_flow
        self._converters = {}

        self._reference_input = self._temperature_node(
            reference_input,
            "ref_input",
        )
        self._reference_output = self._temperature_node(
            reference_output,
            "ref_output",
        )

        self.inbound_interfaces.append(self._reference_input)
        self.outbound_interfaces.append(self._reference_output)

    def _create_converter(self, source, target):
        converter = self.subnode(
            Converter,
            local_name=f"{source.label[0]}->{target.label[0]}",
            inputs={source: MassFlowHeat()},
            outputs={target: MassFlowHeat()},
        )
        self._converters[(source, target)] = converter
        return converter

    def _temperature_node(self, temperature, local_name=None):
        if local_name is None:
            local_name = f"{temperature}"
        node = self.subnode(
            TemperatureBus,
            local_name=local_name,
            temperature=temperature,
            specific_heat_capacity=self.specific_heat_capacity,
        )
        return node


class FixedReturnTemperature(AbstractHeatExchanger):
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
        reservoir_flow: EnergyFlowHeat,
        specific_heat_capacity: float = 1.161,
        parent_node=None,
        custom_properties=None,
    ):
        """
        Initialize space heater.

        :param flow_temperature: Flow temperature
        :param return_temperature: Return temperature
        """

        super().__init__(
            label,
            parent_node=parent_node,
            reference_input=EnergyQuality(flow_temperature, fixed=False),
            reference_output=return_temperature,
            reservoir_flow=reservoir_flow,
            specific_heat_capacity=specific_heat_capacity,
            custom_properties=custom_properties,
        )

        self._flow_temperature = flow_temperature
        self._return_temperature = return_temperature
        self.specific_heat_capacity = specific_heat_capacity

        self._demand_bus = self.subnode(
            Bus,
            local_name="demand",
        )

        self._create_missing_converters()

        self._demand = None

    def _create_missing_converters(self):
        for ii in self.inbound_interfaces:
            for oi in self.outbound_interfaces:
                if (ii, oi) not in self._converters:
                    self._create_converter(ii, oi)

    def _update_conversion_factors(self):
        for nodes, converter in self._converters.items():
            converter.conversion_factors[self._demand] = abs(
                    nodes[0].temperature - nodes[1].temperature
                ) * self.specific_heat_capacity

    def _establish_interconnections(self):
        """Shared establish interconnection code for FixedTemperatureDemands.

        This does not implement establish_interconnections,
        so that the class stays abstract.
        """
        heat_carrier: HeatCarrier = self.parent.get_carrier(HeatCarrier)

        if self.specific_heat_capacity != heat_carrier.specific_heat_capacity:
            raise ValueError("Specific heat capacities need to match")

        input_nodes: list[TemperatureBus] = heat_carrier.nodes_to_connect(
            self._reference_input
        )

        input_node = self._pop_reference_input(input_nodes)
        self.flow_temperature = input_node.temperature
        self._reference_input.inputs[input_node] = MassFlowHeat()

        for input_node in input_nodes:
            new_input = self._inbound_node(input_node.temperature)
            self.inbound_interfaces.append(new_input)
            new_input.inputs[input_node] = MassFlowHeat()

        [output_node] = heat_carrier.nodes_to_connect(
            self._reference_output
        )
        self._reference_output.outputs[output_node] = MassFlowHeat()

    @abstractmethod
    def _inbound_node(self, temperature) -> TemperatureBus:
        pass

    @abstractmethod
    def _pop_reference_input(
        self, nodes: deque[TemperatureBus]
    ) -> TemperatureBus:
        pass


class FixedTemperatureHeating(FixedReturnTemperature):

    def __init__(
        self,
        label,
        *,
        min_flow_temperature: float,
        return_temperature: float,
        time_series: TimeseriesSpecifier,
        specific_heat_capacity: float = 1.161,
        parent_node=None,
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
            flow_temperature=min_flow_temperature,
            return_temperature=return_temperature,
            reservoir_flow=EnergyFlowHeat(
                nominal_capacity=1,
                fix=time_series,
            ),
            specific_heat_capacity=specific_heat_capacity,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        if not min_flow_temperature > return_temperature:
            raise ValueError("Flow must be higher than return temperature")

        self._reference_input.energy_quality.minimum = min_flow_temperature

        self.__build_core()

    def __build_core(self):
        self._demand = self.subnode(
            Sink,
            local_name="sink",
            inputs={self._demand_bus: self._reservoir_flow},
        )
        self._converters[self._reference_input, self._reference_output].outputs[
            self._demand_bus
        ] = MassFlowHeat()
        self._update_conversion_factors()

    def _inbound_node(self, temperature):
        node = super()._temperature_node(temperature)
        self.inbound_interfaces.append(node)
        converter = self._create_converter(node, self._reference_output)
        converter.outputs[self._demand_bus] = EnergyFlowHeat()

        return node

    def _pop_reference_input(self, nodes: deque[TemperatureBus]):
        return nodes.popleft()

    def establish_interconnections(self):
        self._establish_interconnections()
        self._update_conversion_factors()


class FixedTemperatureCooling(FixedReturnTemperature):
    def __init__(
        self,
        label,
        *,
        max_flow_temperature: float,
        return_temperature: float,
        time_series,
        specific_heat_capacity: float = 1.161,
        parent_node=None,
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
            flow_temperature=max_flow_temperature,
            return_temperature=return_temperature,
            reservoir_flow=EnergyFlowHeat(
                nominal_capacity=1,
                fix=time_series,
            ),
            specific_heat_capacity=specific_heat_capacity,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        if not max_flow_temperature < return_temperature:
            raise ValueError("Flow must be lower than return temperature")

        self._reference_input.energy_quality.maximum = max_flow_temperature

        self.__build_core()

    def __build_core(self):
        self._demand = self.subnode(
            Source,
            local_name="source",
            outputs={self._demand_bus: self._reservoir_flow},
        )
        self._converters[self._reference_input, self._reference_output].inputs[
            self._demand_bus
        ] = MassFlowHeat()
        self._update_conversion_factors()

    def _inbound_node(self, temperature):
        node = super()._temperature_node(temperature)
        self.inbound_interfaces.append(node)
        converter = self._create_converter(node, self._reference_output)
        converter.inputs[self._demand_bus] = EnergyFlowHeat()

        return node

    def _pop_reference_input(self, nodes: deque[TemperatureBus]):
        return nodes.pop()

    def establish_interconnections(self):
        self._establish_interconnections()
        self._update_conversion_factors()
