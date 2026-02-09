from oemof.network import Node

from mtress import demands
from mtress.physics import HYDROGEN


def test_basic_initialisation():

    parent_node = Node("parent")
    gd = demands.GasDemand(
        "demand1",
        location=parent_node,
        gas_type=HYDROGEN,
        pressure=40,
        time_series=[1, 2, 3],
    )
    assert gd.label == "demand1"
    assert gd.parent == parent_node
    assert gd._time_series == [1, 2, 3]

    assert len(gd.inbound_interfaces) == 1
    assert len(gd.outbound_interfaces) == 0
