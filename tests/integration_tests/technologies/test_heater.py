from oemof.solph import Results
from oemof.visio import ESGraphRenderer

from mtress import Location, MetaModel, SolphModel, carriers, demands
from mtress._helpers._visualization import graph_graphviz
from mtress.technologies import ResistiveHeater, grid_connection


def test_basic_initialisation():
    energy_system = MetaModel()

    loc = Location("house")

    energy_system.add_location(loc)

    ec = carriers.ElectricityCarrier(location=loc)
    hc = carriers.HeatCarrier(location=loc)

    rh1 = ResistiveHeater(
        "electric_heater",
        location=loc,
        maximum_temperature=60,
    )
    assert rh1.label == ("electric_heater", "house")
    assert rh1.parent == loc

    assert len(rh1.inbound_interfaces) == 2
    assert len(rh1.outbound_interfaces) == 1

    rh2 = ResistiveHeater(
        "electric_hotter",
        location=loc,
        maximum_temperature=100,
        minimum_temperature=20,
    )

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
        path="tests/integration_tests/technologies/test_heater_electric.png"
    )

    solved_model = solph_representation.solve(solve_kwargs={"tee": False})

    myresults = Results(solved_model)
    flows = myresults["flow"]
    solph_representation.graph(
        flow_results=flows,
        path="tests/integration_tests/technologies/test_heater_electric_results.png",
    )


def test_unit():
    from oemof.solph import EnergySystem

    es = EnergySystem()

    rh1 = ResistiveHeater(
        "electric_heater",
        # location=loc,
        maximum_temperature=60,
    )
    assert rh1.label == "electric_heater"
    # assert rh1.parent == loc

    assert len(rh1.inbound_interfaces) == 2
    assert len(rh1.outbound_interfaces) == 1

    rh1.establish_interconnections()

    es.add(rh1)

    graph_graphviz(
        es.nodes,
        path="tests/integration_tests/technologies/test_heater_unit.png",
    )


test_unit()
test_basic_initialisation()
