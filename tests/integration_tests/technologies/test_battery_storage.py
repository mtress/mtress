from oemof.solph import Results

from mtress import Location, MetaModel, SolphModel, carriers
from mtress._helpers._visualization import graph_graphviz
from mtress.technologies import BatteryStorage, grid_connection


def test_basic_initialisation():
    energy_system = MetaModel()

    loc = Location("house")

    energy_system.add_location(loc)

    ec = carriers.ElectricityCarrier(location=loc)

    bs = BatteryStorage(
        "battery",
        location=loc,
        nominal_capacity=1000,
    )
    assert bs.label == ("battery", "house")
    assert bs.parent == loc

    assert len(bs.inbound_interfaces) == 1
    assert len(bs.outbound_interfaces) == 1

    egc = grid_connection.ElectricityGridConnection(
        working_rate=0.3,
        location=loc,
    )

    solph_representation = SolphModel(
        energy_system,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 03:00:00",
            "freq": "60min",
        },
    )

    solph_representation.graph(
        path="tests/integration_tests/technologies/test_battery_storage.png"
    )

    solved_model = solph_representation.solve(solve_kwargs={"tee": False})

    myresults = Results(solved_model)
    flows = myresults["flow"]
    solph_representation.graph(
        flow_results=flows,
        path="tests/integration_tests/technologies/test_battery_storage_results.png",
    )


def test_unit():
    from oemof.solph import EnergySystem

    es = EnergySystem()

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
