from oemof.solph import Model

from mtress import EnergySystem, Location, carriers, demands
from mtress.technologies import grid_connection


def test_basic_initialisation():

    energy_system = EnergySystem(
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 03:00:00",
            "freq": "60min",
        },
    )

    loc = Location("house")

    energy_system.add(loc)

    ec = loc.subnode(
        carriers.ElectricityCarrier,
        local_name="EC",
    )

    ed1 = loc.subnode(
        demands.Electricity,
        local_name="demand1",
        time_series=[1, 2, 3],
    )

    assert ed1.label == ("demand1", "house")
    assert ed1.parent == loc
    assert ed1._time_series == [1, 2, 3]

    assert len(ed1.inbound_interfaces) == 1
    assert len(ed1.outbound_interfaces) == 0

    ed2 = loc.subnode(
        demands.Electricity,
        local_name="demand2",
        time_series=[3, 2, 1],
    )
    assert ed2.label == ("demand2", "house")
    assert ed2.parent == loc
    assert ed2._time_series == [3, 2, 1]

    assert len(ed2.inbound_interfaces) == 1
    assert len(ed2.outbound_interfaces) == 0

    egc = loc.subnode(
        grid_connection.ElectricityGridConnection,
        local_name="EGC",
        working_rate=0.3,
    )

    energy_system.establish_interconnections()

    energy_system.graph(
        path="tests/integration_tests/demands/test_electricity_demand.png"
    )

    model = Model(energy_system)

    results = model.solve()
    flows = results["flow"]

    energy_system.graph(
        flow_results=flows,
        path="tests/integration_tests/demands/test_electricity_demand_results.png",
    )


test_basic_initialisation()
