from oemof.solph import Model

from mtress import EnergySystem, Location, carriers, demands
from mtress.technologies import RenewableElectricitySource, grid_connection


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

    res = loc.subnode(
        RenewableElectricitySource,
        local_name="pv",
        nominal_power=1,
        specific_generation=[1, 2, 3],
    )

    assert res.label == ("pv", "house")
    assert res.parent == loc
    assert res._specific_generation == [1, 2, 3]
    assert res._fixed == True

    assert len(res.inbound_interfaces) == 0
    assert len(res.outbound_interfaces) == 1

    ed = loc.subnode(
        demands.Electricity,
        local_name="demand",
        time_series=[1, 2, 3],
    )

    energy_system.establish_interconnections()

    energy_system.graph(
        path="tests/integration_tests/technologies/test_renewable_electricity_source.png"
    )

    model = Model(energy_system)
    results = model.solve()

    assert (
        results._solver_results.Problem.lower_bound
        == results._solver_results.Problem.upper_bound
    )
    assert results._solver_results.Problem.lower_bound == 0.0

    flows = results["flow"]
    energy_system.graph(
        flow_results=flows,
        path="tests/integration_tests/technologies/test_renewable_electricity_source_results.png",
    )


def test_export():

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

    res = loc.subnode(
        RenewableElectricitySource,
        local_name="pv",
        nominal_power=1,
        specific_generation=[1, 2, 3],
    )

    assert res.label == ("pv", "house")
    assert res.parent == loc
    assert res._specific_generation == [1, 2, 3]
    assert res._fixed == True

    assert len(res.inbound_interfaces) == 0
    assert len(res.outbound_interfaces) == 1

    egc = loc.subnode(
        grid_connection.ElectricityGridConnection,
        local_name="EGC",
        working_rate=0.3,
        revenue=0.06,
    )

    energy_system.establish_interconnections()

    energy_system.graph(
        path="tests/integration_tests/technologies/test_renewable_electricity_source_revenue.png"
    )

    model = Model(energy_system)
    results = model.solve()

    assert (
        results._solver_results.Problem.lower_bound
        == results._solver_results.Problem.upper_bound
    )
    assert results._solver_results.Problem.lower_bound == -0.36

    flows = results["flow"]
    energy_system.graph(
        flow_results=flows,
        path="tests/integration_tests/technologies/test_renewable_electricity_source_revenue_results.png",
    )


def test_export_and_import():

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

    res = loc.subnode(
        RenewableElectricitySource,
        local_name="pv",
        nominal_power=1,
        specific_generation=[1, 2, 3],
    )
    assert res.label == ("pv", "house")
    assert res.parent == loc
    assert res._specific_generation == [1, 2, 3]
    assert res._fixed == True

    assert len(res.inbound_interfaces) == 0
    assert len(res.outbound_interfaces) == 1

    ed = loc.subnode(
        demands.Electricity,
        local_name="demand",
        time_series=[3, 2, 1],
    )

    egc = loc.subnode(
        grid_connection.ElectricityGridConnection,
        local_name="EGC",
        working_rate=0.3,
        revenue=0.06,
    )

    energy_system.establish_interconnections()

    energy_system.graph(
        path="tests/integration_tests/technologies/test_renewable_electricity_source_im_export.png"
    )

    model = Model(energy_system)
    results = model.solve()

    assert (
        results._solver_results.Problem.lower_bound
        == results._solver_results.Problem.upper_bound
    )
    assert results._solver_results.Problem.lower_bound == 0.48

    flows = results["flow"]
    energy_system.graph(
        flow_results=flows,
        path="tests/integration_tests/technologies/test_renewable_electricity_source_im_export_results.png",
    )


test_basic_initialisation()
test_export()
test_export_and_import()
