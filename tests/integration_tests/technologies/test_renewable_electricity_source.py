from oemof.solph import Results
from oemof.visio import ESGraphRenderer

from mtress import Location, MetaModel, SolphModel, _carriers, demands
from mtress.technologies import RenewableElectricitySource, grid_connection


def test_basic_initialisation():

    energy_system = MetaModel()

    loc = Location("house")

    energy_system.add_location(loc)

    ec = _carriers.ElectricityCarrier(location=loc)

    res1 = RenewableElectricitySource(
        "pv1",
        location=loc,
        nominal_power=1,
        specific_generation=[1, 2, 3],
    )
    assert res1.label == ("pv1", "house")
    assert res1.parent == loc
    assert res1._specific_generation == [1, 2, 3]
    assert res1._fixed == True

    assert len(res1.inbound_interfaces) == 0
    assert len(res1.outbound_interfaces) == 1

    ed1 = demands.Electricity("demand1", location=loc, time_series=[1, 2, 3])

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
        path="tests/integration_tests/technologies/test_renewable_electricity_source.png"
    )

    solved_model = solph_representation.solve(solve_kwargs={"tee": False})
    myresults = Results(solved_model)
    assert (
        myresults._solver_results.Problem.lower_bound
        == myresults._solver_results.Problem.upper_bound
    )
    assert myresults._solver_results.Problem.lower_bound == 0.0

    flows = myresults["flow"]
    solph_representation.graph(
        flow_results=flows,
        path="tests/integration_tests/technologies/test_renewable_electricity_source_results.png",
    )


def test_export():

    energy_system = MetaModel()

    loc = Location("house")

    energy_system.add_location(loc)

    ec = _carriers.ElectricityCarrier(location=loc)

    res1 = RenewableElectricitySource(
        "pv1",
        location=loc,
        nominal_power=1,
        specific_generation=[1, 2, 3],
    )
    assert res1.label == ("pv1", "house")
    assert res1.parent == loc
    assert res1._specific_generation == [1, 2, 3]
    assert res1._fixed == True

    assert len(res1.inbound_interfaces) == 0
    assert len(res1.outbound_interfaces) == 1

    egc = grid_connection.ElectricityGridConnection(
        working_rate=0.3,
        revenue=0.06,
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
        path="tests/integration_tests/technologies/test_renewable_electricity_source_revenue.png"
    )

    solved_model = solph_representation.solve(solve_kwargs={"tee": False})
    myresults = Results(solved_model)
    assert (
        myresults._solver_results.Problem.lower_bound
        == myresults._solver_results.Problem.upper_bound
    )
    assert myresults._solver_results.Problem.lower_bound == -0.36

    flows = myresults["flow"]
    solph_representation.graph(
        flow_results=flows,
        path="tests/integration_tests/technologies/test_renewable_electricity_source_revenue_results.png",
    )


def test_export_and_import():

    energy_system = MetaModel()

    loc = Location("house")

    energy_system.add_location(loc)

    ec = _carriers.ElectricityCarrier(location=loc)

    res1 = RenewableElectricitySource(
        "pv1",
        location=loc,
        nominal_power=1,
        specific_generation=[1, 2, 3],
    )
    assert res1.label == ("pv1", "house")
    assert res1.parent == loc
    assert res1._specific_generation == [1, 2, 3]
    assert res1._fixed == True

    assert len(res1.inbound_interfaces) == 0
    assert len(res1.outbound_interfaces) == 1

    ed1 = demands.Electricity("demand1", location=loc, time_series=[3, 2, 1])

    egc = grid_connection.ElectricityGridConnection(
        working_rate=0.3,
        revenue=0.06,
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
        path="tests/integration_tests/technologies/test_renewable_electricity_source_im_export.png"
    )

    solved_model = solph_representation.solve(solve_kwargs={"tee": False})
    myresults = Results(solved_model)
    assert (
        myresults._solver_results.Problem.lower_bound
        == myresults._solver_results.Problem.upper_bound
    )
    assert myresults._solver_results.Problem.lower_bound == 0.48

    flows = myresults["flow"]
    solph_representation.graph(
        flow_results=flows,
        path="tests/integration_tests/technologies/test_renewable_electricity_source_im_export_results.png",
    )


test_basic_initialisation()
test_export()
test_export_and_import()
