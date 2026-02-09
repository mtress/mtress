from oemof.network import Node

from mtress import demands


def test_basic_initialisation():

    parent_node = Node("parent")
    ed = demands.Electricity(
        "demand1", location=parent_node, time_series=[1, 2, 3]
    )
    assert ed.label == "demand1"
    assert ed.parent == parent_node
    assert ed._time_series == [1, 2, 3]

    assert len(ed.inbound_interfaces) == 1
    assert len(ed.outbound_interfaces) == 0
