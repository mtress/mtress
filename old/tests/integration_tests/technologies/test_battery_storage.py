from oemof.solph import Model

from mtress import EnergySystem, Location, carriers, demands
from mtress._helpers._visualization import graph_graphviz
from mtress.technologies import BatteryStorage, grid_connection


def test_basic_initialisation():
    energy_system = EnergySystem(
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 02:00:00",
            "freq": "60min",
        },
    )

    loc = Location("house")

    energy_system.add(loc)

    ec = loc.subnode(
        carriers.ElectricityCarrier,
        local_name="EC",
    )

    bs = loc.subnode(
        BatteryStorage,
        local_name="battery",
        nominal_capacity=1000,
    )

    assert bs.label == ("battery", "house")
    assert bs.parent == loc

    assert len(bs.inbound_interfaces) == 1
    assert len(bs.outbound_interfaces) == 1

    ed = loc.subnode(
        demands.Electricity,
        local_name="demand",
        time_series=[0, 10],
    )

    egc = loc.subnode(
        grid_connection.ElectricityGridConnection,
        local_name="EGC",
        working_rate=[0, 0.3],
    )

    energy_system.establish_interconnections()

    energy_system.graph(
        path="tests/integration_tests/technologies/test_battery_storage.png"
    )

    model = Model(energy_system)

    results = model.solve()
    flows = results["flow"]
    energy_system.graph(
        flow_results=flows,
        path="tests/integration_tests/technologies/test_battery_storage_results.png",
    )


def test_unit():
    from oemof.solph import EnergySystem as ESSolph

    es = ESSolph()

    bs = BatteryStorage(
        "battery",
        nominal_capacity=1000,
    )
    assert bs.label == "battery"

    assert len(bs.inbound_interfaces) == 1
    assert len(bs.outbound_interfaces) == 1

    # shouldnt do anything (no parent / location)
    bs.establish_interconnections()

    es.add(bs)

    graph_graphviz(
        es.nodes,
        path="tests/integration_tests/technologies/test_battery_storage_unit.png",
    )


test_unit()
test_basic_initialisation()
