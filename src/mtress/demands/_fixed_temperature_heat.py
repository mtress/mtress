"""Room heating technologies."""

from abc import abstractmethod

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
from .._base_mtress_nodes import AbstractDemand


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
            custom_properties=custom_properties,
        )

        self._flow_temperature = flow_temperature
        self._return_temperature = return_temperature
        self.specific_heat_capacity = specific_heat_capacity

        self._time_series = time_series

        self.__build_core()

    def __build_core(self):
        self._reference_input = self.subnode(
            TemperatureBus,
            local_name=f"reference",
            temperature=self._flow_temperature,
            specific_heat_capacity=self.specific_heat_capacity,
        )

        self._output_node = self.subnode(
            TemperatureBus,
            local_name=f"{self._return_temperature}",
            temperature=EnergyQuality(self._return_temperature, fixed=True),
            specific_heat_capacity=self.specific_heat_capacity,
        )

        self.inbound_interfaces[EnergyType.HEAT] = [self._reference_input]
        self.outbound_interfaces[EnergyType.HEAT] = [self._output_node]

        self._converters = {}
        self._demand_bus = self.subnode(
            Bus,
            local_name="demand",
        )

        self._create_missing_converters()

        self._demand = None

    def _create_missing_converters(self):
        for ii in self.inbound_interfaces[EnergyType.HEAT]:
            for oi in self.outbound_interfaces[EnergyType.HEAT]:
                if (ii, oi) not in self._converters:
                    self._converters[(ii, oi)] = self.subnode(
                        Converter,
                        local_name=f"{ii.label[0]}->{oi.label[0]}",
                        inputs={self._reference_input: MassFlowHeat()},
                        outputs={self._output_node: MassFlowHeat()},
                    )

    def _update_conversion_factors(self):
        for nodes, converter in self._converters.items():
            converter.conversion_factors[self._demand] = abs(
                    self._reference_input.temperature - self._output_node.temperature
                ) * self.specific_heat_capacity

    @abstractmethod
    def _connect_demand(self):
        pass

    def _establish_interconnections(self):
        """Shared establish interconnection code for all HeatExchangers.

        This does not implement establish_interconnections,
        so that the class stays abstract.
        """
        heat_carrier: HeatCarrier = self.parent.get_carrier(HeatCarrier)

        if self.specific_heat_capacity != heat_carrier.specific_heat_capacity:
            raise ValueError("Specific heat capacities need to match")

        input_node: TemperatureBus = heat_carrier.nodes_to_connect(
            self._reference_input
        )[0]
        self.flow_temperature = input_node.temperature
        self._reference_input.inputs[input_node] = MassFlowHeat()

        output_node: TemperatureBus = heat_carrier.nodes_to_connect(
            self._output_node
        )[0]
        self._output_node.outputs[output_node] = MassFlowHeat()


class FixedTemperatureHeating(AbstractFixedTemperature):

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
            time_series=time_series,
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
            inputs={
                self._demand_bus: EnergyFlowHeat(
                    nominal_capacity=1,
                    fix=self._time_series,
                )
            },
        )
        self._connect_demand()
        self._update_conversion_factors()

    def _connect_demand(self):
        for converter in self._converters.values():
            converter.outputs[self._demand_bus] = MassFlowHeat()


    def establish_interconnections(self):
        self._establish_interconnections()


class FixedTemperatureCooling(AbstractFixedTemperature):
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
            time_series=time_series,
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
            outputs={
                self._converters: EnergyFlowHeat(
                    nominal_capacity=1,
                    fix=self._time_series,
                )
            },
        )
        self._connect_demand()
        self._update_conversion_factors()

    def _connect_demand(self):
        for converter in self._converters.values():
            converter.inputs[self._demand_bus] = EnergyFlowHeat()

    def establish_interconnections(self):
        if self.parent:
            heat_carrier: HeatCarrier = self.parent.get_carrier(HeatCarrier)

            _, self.flow_temperature = heat_carrier.get_surrounding_levels(
                self.max_flow_temperature
            )

        self._establish_interconnections()
        self._update_conversion_factors()
