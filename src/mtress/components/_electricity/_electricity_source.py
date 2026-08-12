from oemof.solph.components import Source

from ..._base_mtress_nodes import AbstractTechnology
from ...carriers import ElectricityCarrier
from ...carriers.electricity import ElectricityBus, EnergyFlowElectricity


class ElectricitySource(AbstractTechnology):

    def __init__(
        self,
        label,
        *,
        nominal_power: float,
        parent_node=None,
        custom_properties=None,
    ):
        """
        Electricity source.

        :param nominal_power: nominal power of electricity source
        """
        super().__init__(
            label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        self.nominal_power = nominal_power

        self.__build_core()

    def __build_core(self):
        self._output = self.subnode(
            ElectricityBus,
            local_name="output",
        )

        self.outbound_interfaces.add(self._output)

        self._source_flow = EnergyFlowElectricity(
            nominal_capacity=self.nominal_power
        )

        self._source = self.subnode(
            Source,
            local_name="source",
            outputs={self._output: self._source_flow},
        )

    def establish_interconnections(self):
        electricity_carrier: ElectricityCarrier = self.parent.get_carrier(
            ElectricityCarrier
        )

        self._output.outputs[electricity_carrier.distribution] = (
            EnergyFlowElectricity()
        )
