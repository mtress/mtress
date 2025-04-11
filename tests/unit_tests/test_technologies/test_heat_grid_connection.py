import math
import pytest
from oemof.solph.processing import meta_results, results
from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)


class TestHeatGrid:

    def test_grid_initialisation(self):
        grid_working_rate = None
        grid_revenue = None
        flow_temperature = 30
        return_temperature = 10

        grid = technologies.HeatGridConnection(
            working_rate=grid_working_rate,
            revenue=grid_revenue,
            maximum_temperature=flow_temperature,
            minimum_temperature=return_temperature,
        )
        assert grid.working_rate == grid_working_rate
        assert grid.revenue == grid_revenue
        assert grid.maximum_temperature == flow_temperature
        assert grid.minimum_temperature == return_temperature

    @pytest.mark.parametrize(
        "max_temperature, min_temperature, grid_import_limit, expected_result",
        [(30, 20, None, 400), (55, 20, 10, 544.53)],
    )
    def test_heatgrid(
        self,
        max_temperature,
        min_temperature,
        grid_import_limit,
        expected_result,
    ):
        energy_system = MetaModel()

        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(technologies.SlackNode(penalty=100))

        house_1.add(
            carriers.HeatCarrier(
                temperature_levels=[10, 20, 30, 55],
            )
        )
        house_1.add(
            technologies.HeatGridConnection(
                maximum_temperature=max_temperature,
                minimum_temperature=min_temperature,
                working_rate=10,
                grid_import_limit=grid_import_limit,
            )
        )
        house_1.add(
            demands.FixedTemperatureHeating(
                name="space_heating",
                min_flow_temperature=30,
                return_temperature=20,
                time_series=[20, 20],
            )
        )
        solph_representation = SolphModel(
            energy_system,
            timeindex={
                "start": "2021-07-10 00:00:00",
                "end": "2021-07-10 02:00:00",
                "freq": "60min",
            },
        )

        solph_representation.build_solph_model()
        solved_model = solph_representation.solve(solve_kwargs={"tee": True})
        mr = meta_results(solved_model)

        assert (
            solved_model.solver_results.Solver.Termination_condition
            == "optimal"
        )
        assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)

    @pytest.mark.parametrize(
        "max_temperature, min_temperature, grid_import_limit, expected_result",
        [(30, 20, None, 1200), (55, 20, 20, 1778.12)],
    )
    def test_heatgrid_locations(
        self,
        max_temperature,
        min_temperature,
        grid_import_limit,
        expected_result,
    ):
        energy_system = MetaModel()

        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(technologies.SlackNode(penalty=100))
        house_1.add(
            carriers.HeatCarrier(
                temperature_levels=[10, 20, 30, 55],
            )
        )
        house_1.add(
            technologies.HeatGridConnection(
                working_rate=10,
                maximum_temperature=max_temperature,
                minimum_temperature=min_temperature,
                grid_import_limit=grid_import_limit,
            )
        )
        house_1.add(
            technologies.HeatGridInterconnection(
                maximum_working_temperature=max_temperature,
                minimum_working_temperature=min_temperature,
            )
        )
        house_2 = Location(name="house_2")
        energy_system.add_location(house_2)
        house_2.add(
            carriers.HeatCarrier(
                temperature_levels=[10, 20, 30, 55],
            )
        )
        house_2.add(
            technologies.HeatGridInterconnection(
                maximum_working_temperature=max_temperature,
                minimum_working_temperature=min_temperature,
            )
        )
        house_2.add(
            demands.FixedTemperatureHeating(
                name="space_heating",
                min_flow_temperature=30,
                return_temperature=20,
                time_series=[60, 60],
            )
        )
        solph_representation = SolphModel(
            energy_system,
            timeindex={
                "start": "2021-07-10 00:00:00",
                "end": "2021-07-10 02:00:00",
                "freq": "60min",
            },
        )
        house_1.connect(
            connection=technologies.HeatGridInterconnection,
            destination=house_2,
        )

        solph_representation.build_solph_model()
        solved_model = solph_representation.solve(solve_kwargs={"tee": True})

        mr = meta_results(solved_model)

        assert (
            solved_model.solver_results.Solver.Termination_condition
            == "optimal"
        )
        assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)

    @pytest.mark.parametrize(
        "max_temperature, min_temperature, revenue, grid_export_limit, "
        "expected_result",
        [(55, 20, 100, None, 1200), (55, 20, 100, None, 1200)],
    )
    def test_heatgrid_export(
        self,
        max_temperature,
        min_temperature,
        revenue,
        grid_export_limit,
        expected_result,
    ):
        energy_system = MetaModel()

        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(technologies.SlackNode(penalty=1000))
        house_1.add(
            carriers.HeatCarrier(
                temperature_levels=[10, 20, 30, 55],
            )
        )
        house_1.add(carriers.ElectricityCarrier())

        house_1.add(technologies.ElectricityGridConnection(working_rate=0.0))
        house_1.add(
            technologies.HeatGridConnection(
                working_rate=10,
                maximum_temperature=max_temperature,
                minimum_temperature=min_temperature,
                grid_export_limit=grid_export_limit,
                revenue=revenue,
            )
        )
        house_1.add(
            technologies.HeatPump(
                name="HeatPump",
                thermal_power_limit=100,
                max_temp_primary=20,
                min_temp_primary=10,
                max_temp_secondary=55,
                min_temp_secondary=30,
            )
        )
        house_1.add(
            technologies.HeatSource(
                name="Air_HE",
                reservoir_temperature=20,
                maximum_working_temperature=55,
                minimum_working_temperature=10,
                nominal_power=1e4,
            )
        )
        solph_representation = SolphModel(
            energy_system,
            timeindex={
                "start": "2021-07-10 00:00:00",
                "end": "2021-07-10 02:00:00",
                "freq": "60min",
            },
        )
        solph_representation.build_solph_model()
        solved_model = solph_representation.solve(solve_kwargs={"tee": True})

        mr = meta_results(solved_model)

        assert (
            solved_model.solver_results.Solver.Termination_condition
            == "optimal"
        )
        assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)


if __name__ == "__main__":

    import os
    from oemof.solph.processing import results, meta_results
    from mtress import (
        Location,
        MetaModel,
        SolphModel,
        carriers,
        demands,
        technologies,
    )
    from mtress._helpers import get_flows

    os.chdir(os.path.dirname(__file__))
    energy_system = MetaModel()

    house_1 = Location(name="house_1")
    energy_system.add_location(house_1)

    # house_1.add(technologies.SlackNode(penalty=1000))

    house_1.add(
        carriers.HeatCarrier(
            temperature_levels=[10, 20, 30, 55],
        )
    )
    house_1.add(carriers.ElectricityCarrier())

    house_1.add(technologies.ElectricityGridConnection(working_rate=0.0))

    house_1.add(
        technologies.HeatGridConnection(
            maximum_temperature=55,
            minimum_temperature=20,
            grid_export_limit=None,
            working_rate=0,
            revenue=100,
        )
    )

    house_1.add(
        technologies.HeatPump(
            name="HeatPump",
            thermal_power_limit=100,
            max_temp_primary=20,
            min_temp_primary=10,
            max_temp_secondary=55,
            min_temp_secondary=30,
        )
    )

    house_1.add(
        technologies.HeatSource(
            name="Air_HE",
            reservoir_temperature=20,
            maximum_working_temperature=55,
            minimum_working_temperature=10,
            nominal_power=1e4,
        )
    )

    solph_representation = SolphModel(
        energy_system,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 02:00:00",
            "freq": "60min",
        },
    )

    solph_representation.build_solph_model()
    solved_model = solph_representation.solve(solve_kwargs={"tee": True})

    myresults = results(solved_model)
    flows = get_flows(myresults)
    mr = meta_results(solved_model)

    plot = solph_representation.graph(detail=True, flow_results=flows)
    plot.render(outfile="heat_grid_export.png")

    print("cost is: ", mr["objective"])
