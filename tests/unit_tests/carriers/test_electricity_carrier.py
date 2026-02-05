from oemof.network import Node

from mtress.carriers import ElectricityCarrier


def test_basic_initialisation():
    parent_node = Node("parent")
    ec = ElectricityCarrier(parent_node=parent_node)
    assert ec.label == "ElectricityCarrier"
    assert ec.parent == parent_node

    assert len(ec._inbound_interfaces) == 2
    assert len(ec._outbound_interfaces) == 2
