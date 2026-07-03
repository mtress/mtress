from mtress import EnergySystem
from mtress import Location
from mtress.carriers import HeatCarrier
from mtress.demands import FixedTemperatureCooling


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
        FixedTemperatureCooling,
        local_name="cooling_demand",
        max_flow_temperature=10,
        return_temperature=20,
        time_series=[50, 50],
    )

    loc.subnode(
        HeatCarrier,
        local_name="HC",
        temperature_levels=[
            2,  # inbound
            5,  # inbound
            10,  # inbound
            [9, 11],  # inbound (lowest / reference)
            [19, 21],
            20,  # outbound
            [30, 30.5],
        ],
    )

    energy_system.establish_interconnections()

    assert list(hd.inbound_interfaces.keys()) == [HeatCarrier]
    assert list(hd.outbound_interfaces.keys()) == [HeatCarrier]

    assert len(hd.inbound_interfaces[HeatCarrier]) == 4
    oi = hd.outbound_interfaces[HeatCarrier]
    assert len(oi) == 1
    assert oi[0] == "('20', 'cooling_demand', 'loc')"
