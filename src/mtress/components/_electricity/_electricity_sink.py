from oemof.solph.components import Sink

from ..._base_mtress_nodes import AbstractTechnology
from ...carriers import ElectricityCarrier
from ...carriers.electricity import ElectricityBus, EnergyFlowElectricity


class ElectricitySink(AbstractTechnology):

    def __init__(
        self,
        label,
        *,
        nominal_power: float,
        parent_node=None,
        custom_properties=None,
    ):
        """
        Electricity sink.

        :param nominal_power: nominal power of electricity sink
        """
        super().__init__(
            label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        self.nominal_power = nominal_power

        self.__build_core()

    def __build_core(self):
        self._input = self.subnode(
            ElectricityBus,
            local_name="input",
        )

        self.inbound_interfaces.add(self._input)

        self._sink_flow = EnergyFlowElectricity(
            nominal_capacity=self.nominal_power
        )

        self._sink = self.subnode(
            Sink,
            local_name="sink",
            inputs={self._input: self._sink_flow},
        )

    def establish_interconnections(self):
        electricity_carrier: ElectricityCarrier = self.parent.get_carrier(
            ElectricityCarrier
        )

        self._input.inputs[electricity_carrier.distribution] = (
            EnergyFlowElectricity()
        )
