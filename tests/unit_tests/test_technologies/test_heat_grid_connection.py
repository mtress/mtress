from oemof.solph.processing import meta_results

from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)


def test_heat_grid_example():

    energy_system = MetaModel()

    house_1 = Location(name="house_1")
    energy_system.add_location(house_1)

    house_1.add(
        carriers.HeatCarrier(
            temperature_levels=[10, 20, 30, 55],
            reference_temperature=0,
        )
    )
    house_1.add(
        demands.FixedTemperatureHeating(
            name="space_heating",
            min_flow_temperature=30,
            return_temperature=20,
            time_series=[50, 60],
        )
    )

    house_1.add(
        technologies.HeatGridConnection(
            working_rate=10,
            maximum_working_temperature=30,
            minimum_working_temperature=20,
            revenue=0,
        )
    )

    solph_representation = SolphModel(
        energy_system,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 02:00:00",
            "freq": "60T",
        },
    )

    solph_representation.build_solph_model()
    solved_model = solph_representation.solve(solve_kwargs={"tee": True})
    mr = meta_results(solved_model)

    price_heat_consumption = 1100.0

    assert (
        solved_model.solver_results.Solver.Termination_condition == "optimal"
    )
    assert mr["objective"] == price_heat_consumption


def test_grid_initialisation():
    grid_working_rate = None
    grid_revenue = None

    grid = technologies.HeatGridConnection(
        working_rate=grid_working_rate,
        revenue=grid_revenue,
    )

    assert grid.working_rate == grid_working_rate
    assert grid.revenue == grid_revenue
