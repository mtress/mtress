from oemof.solph import Results

from mtress import Location, MetaModel, SolphModel, _carriers, demands
from mtress.technologies import grid_connection


def test_basic_initialisation():

    energy_system = MetaModel()

    loc = Location("house")

    energy_system.add_location(loc)

    ec = _carriers.ElectricityCarrier(label="ec", parent_node=loc)

    egc = grid_connection.ElectricityGridConnection(
        working_rate=0.3, location=loc
    )

    solph_representation = SolphModel(
        energy_system,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 01:00:00",
            "freq": "60min",
        },
    )

    solph_representation.graph(
        path="tests/integration_tests/grid_connection/test_electricity_grid.png"
    )

    solved_model = solph_representation.solve(solve_kwargs={"tee": False})

    myresults = Results(solved_model)
    flows = myresults["flow"]
    solph_representation.graph(
        flow_results=flows,
        path="tests/integration_tests/grid_connection/test_electricity_grid_results.png",
    )


def test_connection():

    energy_system = MetaModel()

    loc1 = Location("house 1")
    loc2 = Location("house 2")

    energy_system.add_location(loc1)
    energy_system.add_location(loc2)

    ec1 = _carriers.ElectricityCarrier(location=loc1)
    ec2 = _carriers.ElectricityCarrier(location=loc2)

    egc1 = grid_connection.ElectricityGridConnection(
        working_rate=0.3, location=loc1
    )
    egc2 = grid_connection.ElectricityGridConnection(
        working_rate=0.3, location=loc2
    )

    egc1.connect(egc2)

    solph_representation = SolphModel(
        energy_system,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 01:00:00",
            "freq": "60min",
        },
    )

    solph_representation.graph(
        path="tests/integration_tests/grid_connection/test_electricity_grid_connection.png"
    )

    solved_model = solph_representation.solve(solve_kwargs={"tee": False})

    myresults = Results(solved_model)
    flows = myresults["flow"]
    solph_representation.graph(
        flow_results=flows,
        path="tests/integration_tests/grid_connection/test_electricity_grid_connection_results.png",
    )


test_basic_initialisation()
test_connection()
