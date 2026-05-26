from oemof.network import Node

from mtress import demands


def test_basic_initialisation():

    ed = demands.Electricity(
        label="demand1", time_series=[1, 2, 3]
    )
    assert ed._time_series == [1, 2, 3]

    assert len(ed.inbound_interfaces) == 1
    assert len(ed.outbound_interfaces) == 0
