"""Room heating technologies."""

from abc import abstractmethod
from collections import deque

from oemof.solph import Bus, Flow
from oemof.solph.components import Sink, Source

from mtress._plumbing import (
    maxseq,
    minseq,
)

from ..._energy_types import EnergyFlowHeat
from ..._energy_types import EnergyQuality
from ..._energy_types import MassFlowHeat
from ..._energy_types import TemperatureBus
from ..._data_handler import TimeseriesSpecifier
from ...carriers import HeatCarrier

from ._abstract_heat_exchanger import AbstractHeatExchanger


class IncrementalTemperature(AbstractHeatExchanger):

    def __init__(
        self,
        label,
        *,
        reference_input,
        reference_output,
        reservoir_flow,
        minimum_delta_medium: float = 1.0,
        conductivity_gain_factor: float | None = None,
        non_thermal_gains=0,
        reservoir_costs=0,
        parent_node=None,
        custom_properties=None,
    ):
        super().__init__(
            label,
            parent_node=parent_node,
            reference_input=reference_input,
            reference_output=reference_output,
            reservoir_flow=reservoir_flow,
            specific_heat_capacity=1.161,
            custom_properties=parent_node,
        )


class SteppedReturnHeating(IncrementalTemperature):

    def __init__(
        self,
        label,
        reservoir_temperature: TimeseriesSpecifier,
        nominal_power: float,
        minimum_working_temperature: float = 0,
        maximum_working_temperature: float = 100,
        minimum_delta_medium: float = 1.0,
        minimum_delta_reservoir: float = 1.0,
        conductivity_gain_factor: float | None = None,
        non_thermal_gains = 0,
        working_rate = 0,
        parent_node=None,
        custom_properties=None,
    ):
        lowest_temperature = maxseq(
            reservoir_temperature,
            minimum_working_temperature,
        )
        min_output_temperature = (
            lowest_temperature
            + minimum_delta_reservoir
        )
        reference_input = EnergyQuality(
            value=min_output_temperature + minimum_delta_medium,
            maximum=maximum_working_temperature,
            minimum=min_output_temperature + minimum_delta_medium,
        )
        reference_output = EnergyQuality(
            value=min_output_temperature,
            maximum=maximum_working_temperature - minimum_delta_medium,
            minimum=min_output_temperature,
        )
        super().__init__(
            label=label,
            reference_input=reference_input,
            reference_output=reference_output,
            reservoir_flow=EnergyFlowHeat(nominal_capacity=nominal_power),
            minimum_delta_medium=minimum_delta_medium,
            conductivity_gain_factor=conductivity_gain_factor,
            non_thermal_gains=non_thermal_gains,
            reservoir_costs=working_rate,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        self._reservoir = self.subnode(
            TemperatureBus,
            temperature=reservoir_temperature,
            local_name="reservoir",
        )
        self.subnode(
            Sink,
            local_name="sink_reservoir",
            inputs={self._reservoir: self._reservoir_flow},
        )

        self._utilisation = self.subnode(
            Bus,
            local_name="utilisation",
        )
        self.subnode(
            Source,
            local_name="source_utilisation",
            outputs={self._utilisation: Flow(nominal_capacity=1)},
        )

        self._create_converter(self._reference_input, self._reference_output)

        converter = self._converters[
            (self._reference_input, self._reference_output)
        ]
        converter.inputs[self._utilisation] = Flow()
        converter.outputs[self._reservoir] = EnergyFlowHeat()

    def _create_missing_converters(self):
        pass

    def _update_conversion_factors(self):
        for nodes, converter in self._converters.items():
            converter.conversion_factors[self._reservoir] = (
                abs(nodes[0].temperature - nodes[1].temperature)
                * self.specific_heat_capacity
            )

    def establish_interconnections(self):
        """Shared establish interconnection code for FixedTemperatureDemands.

        This does not implement establish_interconnections,
        so that the class stays abstract.
        """
        heat_carrier: HeatCarrier = self.parent.get_carrier(HeatCarrier)

        if self.specific_heat_capacity != heat_carrier.specific_heat_capacity:
            raise ValueError("Specific heat capacities need to match")

        self._create_io_nodes(
            input_nodes=heat_carrier.nodes_to_connect(self._reference_input),
            output_nodes=heat_carrier.nodes_to_connect(self._reference_output),
        )

    def _create_io_nodes(
        self,
        input_nodes: deque[TemperatureBus],
        output_nodes: deque[TemperatureBus],
    ):
        output_node = self._pop_next_node(output_nodes)
        self._reference_output.outputs[output_node] = MassFlowHeat()

        input_node = self._pop_next_node(input_nodes)

        while (output_nodes[0] is not input_node):
            output_node = self._pop_next_node(output_nodes)
            obn = self._outbound_node(output_node.temperature)
            obn.outputs[output_node] = MassFlowHeat()

        io_node = self._pop_next_node(output_nodes)
        trn = self._transitional_node(io_node.temperature)
        trn.outputs[io_node] = MassFlowHeat()
        trn.inputs[io_node] = MassFlowHeat()

    def _inbound_node(self, temperature) -> TemperatureBus:
        node = super()._temperature_node(temperature)
        self.inbound_interfaces.append(node)

        return node

    def _outbound_node(self, temperature) -> TemperatureBus:
        node = super()._temperature_node(temperature)
        self.outbound_interfaces.append(node)

        return node

    def _transitional_node(self, temperature) -> TemperatureBus:
        node = super()._temperature_node(temperature)

        self.inbound_interfaces.append(node)
        self.outbound_interfaces.append(node)

        return node

    def _pop_next_node(
        self, nodes: deque[TemperatureBus]
    ) -> TemperatureBus:
        return nodes.popleft()
