from oemof.network import Node

from mtress import demands


def test_basic_initialisation_heating():

    hd = demands.FixedTemperatureHeating(
        label="demand1",
        min_flow_temperature=40,
        return_temperature=30,
        time_series=[1, 2, 3],
    )
    assert hd._time_series == [1, 2, 3]
    assert hd.min_flow_temperature == 40
    assert hd.return_temperature == 30

    assert len(hd.inbound_interfaces) == 1
    assert len(hd.outbound_interfaces) == 1


def test_basic_initialisation_cooling():

    cd = demands.FixedTemperatureCooling(
        label="demand1",
        return_temperature=40,
        max_flow_temperature=20,
        time_series=[1, 2, 3],
    )
    assert cd._time_series == [1, 2, 3]
    assert cd.return_temperature == 40
    assert cd.max_flow_temperature == 20

    assert len(cd.inbound_interfaces) == 1
    assert len(cd.outbound_interfaces) == 1
