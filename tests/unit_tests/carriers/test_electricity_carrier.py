from oemof.network import Node

from mtress._constants import EnergyType
from mtress.carriers import ElectricityCarrier


def test_basic_initialisation():
    parent_node = Node("parent")
    ec = ElectricityCarrier(parent_node=parent_node)
    assert ec.label == ("ElectricityCarrier", "parent")
    assert ec.parent == parent_node

    assert len(ec.inbound_interfaces[EnergyType.ELECTRICITY]) == 2
    assert len(ec.outbound_interfaces[EnergyType.ELECTRICITY]) == 2
