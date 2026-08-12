from oemof.solph.components import Converter

from ...carriers.heat import EnergyFlowHeat
from ...carriers.heat import MassFlowHeat
from ...carriers.heat import TemperatureBus
from ..._base_mtress_nodes import AbstractTechnology


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

        self.inbound_interfaces.add(self._reference_input)
        self.outbound_interfaces.add(self._reference_output)

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
