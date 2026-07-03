from mtress import EnergySystem
from mtress import Location
from mtress.carriers import HeatCarrier
from mtress.demands import FixedTemperatureHeating


def test_establish_interconnections():
    energy_system = EnergySystem(
        timeindex={
            "start": "2022-01-10 00:00:00",
            "end": "2022-01-10 02:00:00",
            "freq": "60min",
        },
    )

    loc = Location(label="loc")
    energy_system.add(loc)

    # Add demands
    hd = loc.subnode(
        FixedTemperatureHeating,
        local_name="heat_demand",
        min_flow_temperature=20,
        return_temperature=10,
        time_series=[50, 50],
    )

    loc.subnode(
        HeatCarrier,
        local_name="HC",
        temperature_levels=[
            2,
            5,
            10,  # outbound
            11,
            [19, 21],  # inbound (lowest / reference)
            20,  # inbound
            [30, 30.5],  # inbound
        ],
    )

    energy_system.establish_interconnections()

    assert list(hd.inbound_interfaces.keys()) == [HeatCarrier]
    assert list(hd.outbound_interfaces.keys()) == [HeatCarrier]

    assert len(hd.inbound_interfaces[HeatCarrier]) == 3
    oi = hd.outbound_interfaces[HeatCarrier]
    assert len(oi) == 1
    assert oi[0] == "('10', 'heat_demand', 'loc')"
