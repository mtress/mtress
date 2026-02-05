from abc import ABC
from abc import abstractmethod

from oemof import solph
from oemof.network import Node

from ._constants import EnergyType


class SubNetwork(ABC, Node):
    def __init__(
        self,
        label,
        *,
        parent_node=None,
        custom_properties=None,
    ):
        super().__init__(
            label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        self._inbound_interfaces: dict[EnergyType : list[solph.Bus]] = {}
        self._outbound_interfaces: dict[EnergyType : list[solph.Bus]] = {}

    @abstractmethod
    def establish_interconnections(self):
        pass

    def add_constraints(self, model: solph.Model):
        pass
