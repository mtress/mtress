from oemof.solph import Results

from mtress import Location, MetaModel, SolphModel, _carriers, demands
from mtress.technologies import grid_connection


def test_basic_initialisation():

    energy_system = MetaModel()

    loc = Location("house")

    energy_system.add_location(loc)

    ec = _carriers.ElectricityCarrier(location=loc)

    ed1 = demands.Electricity("demand1", location=loc, time_series=[1, 2, 3])
    assert ed1.label == ("demand1", "house")
    assert ed1.parent == loc
    assert ed1._time_series == [1, 2, 3]

    assert len(ed1.inbound_interfaces) == 1
    assert len(ed1.outbound_interfaces) == 0

    ed2 = demands.Electricity("demand2", location=loc, time_series=[3, 2, 1])
    assert ed2.label == ("demand2", "house")
    assert ed2.parent == loc
    assert ed2._time_series == [3, 2, 1]

    assert len(ed2.inbound_interfaces) == 1
    assert len(ed2.outbound_interfaces) == 0

    egc = grid_connection.ElectricityGridConnection(
        working_rate=0.3, location=loc
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
        path="tests/integration_tests/demands/test_electricity_demand.png"
    )

    solved_model = solph_representation.solve(solve_kwargs={"tee": False})

    myresults = Results(solved_model)
    flows = myresults["flow"]
    solph_representation.graph(
        flow_results=flows,
        path="tests/integration_tests/demands/test_electricity_demand_results.png",
    )


test_basic_initialisation()
