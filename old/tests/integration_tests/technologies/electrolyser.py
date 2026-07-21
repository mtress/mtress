from oemof.solph import Results
from mtress.technologies._electrolyser import ElectrolyserTemplate
from mtress import Location, MetaModel, SolphModel, demands
from mtress import carriers
from mtress._helpers._visualization import graph_graphviz
from mtress.technologies import ResistiveHeater, grid_connection, Electrolyser
from mtress.physics import HYDROGEN
from mtress.technologies import AFC, PEM_ELECTROLYSER


def test_basic_initialisation():
    energy_system = MetaModel()

    loc = Location("house")

    energy_system.add_location(loc)

    ec = carriers.ElectricityCarrier(parent_node=loc, label="c")
    hc = carriers.HeatCarrier(parent_node=loc, label="ce")

    rh1 = Electrolyser(
        "electrolyser", nominal_power=100e3, template=PEM_ELECTROLYSER
    )

    electricity = grid_connection.ElectricityGridConnection(working_rate=0)

    gas_grid = grid_connection.GasGridConnection(
        gas_type=HYDROGEN,
        grid_pressure=30,
        revenue=10,
        working_rate=0,
    )
    assert rh1.label == ("electrolyser", "house")
    assert rh1.parent == loc

    assert len(rh1.inbound_interfaces) == 1
    assert len(rh1.outbound_interfaces) == 2

    solph_representation = SolphModel(
        energy_system,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 03:00:00",
            "freq": "60min",
        },
    )

    solph_representation.graph(
        path="tests/integration_tests/technologies/electrolyser.png"
    )

    solved_model = solph_representation.solve(solve_kwargs={"tee": False})

    myresults = Results(solved_model)
    flows = myresults["flow"]
    solph_representation.graph(
        flow_results=flows,
        path="tests/integration_tests/technologies/test_electrolyser.png",
    )


test_basic_initialisation()
