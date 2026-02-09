from oemof.network import Node

from mtress import demands


def test_basic_initialisation_heating():

    parent_node = Node("parent")
    hd = demands.FixedTemperatureHeating(
        "demand1",
        location=parent_node,
        min_flow_temperature=40,
        return_temperature=30,
        time_series=[1, 2, 3],
    )
    assert hd.label == "demand1"
    assert hd.parent == parent_node
    assert hd._time_series == [1, 2, 3]
    assert hd.flow_temperature == 40
    assert hd.return_temperature == 30

    assert len(hd.inbound_interfaces) == 1
    assert len(hd.outbound_interfaces) == 1


def test_basic_initialisation_cooling():

    parent_node = Node("parent")
    cd = demands.FixedTemperatureCooling(
        "demand1",
        location=parent_node,
        return_temperature=40,
        max_flow_temperature=20,
        flow_temperature=30,
        time_series=[1, 2, 3],
    )
    assert cd.label == "demand1"
    assert cd.parent == parent_node
    assert cd._time_series == [1, 2, 3]
    assert cd.return_temperature == 40
    assert cd.max_flow_temperature == 20
    assert cd.flow_temperature == 30

    assert len(cd.inbound_interfaces) == 1
    assert len(cd.outbound_interfaces) == 1
