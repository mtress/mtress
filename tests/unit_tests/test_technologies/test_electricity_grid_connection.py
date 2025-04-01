from mtress.technologies import ElectricityGridConnection
from oemof.solph.processing import meta_results, results
import math
import pytest
from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress._helpers import get_flows


class TestGridConnection:

    def test_grid_initialisation(self):
        grid_working_rate = None
        grid_demand_rate = None
        grid_import_limit = None

        grid = ElectricityGridConnection(
            working_rate=grid_working_rate,
            demand_rate=grid_demand_rate,
            grid_import_limit=grid_import_limit,
        )

        assert grid.working_rate == grid_working_rate
        assert grid.demand_rate == grid_demand_rate
        assert grid.grid_import_limit == grid_import_limit

    @pytest.mark.parametrize(
        "grid_limit, expected_result",
        [(10, 300.0), (None, 210.0)],
    )
    def test_grid_imports_example(self, grid_limit, expected_result):

        energy_system = MetaModel()

        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(
            technologies.ElectricityGridConnection(
                working_rate=10, grid_import_limit=grid_limit
            )
        )
        house_1.add(
            demands.Electricity(
                name="electricity demand",
                time_series=[11, 10],
            )
        )
        house_1.add(technologies.SlackNode(penalty=100))
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

        myresults = results(solved_model)
        flows = get_flows(myresults)

        grid_flow = flows[
            ("house_1", "ElectricityGridConnection", "source_import"),
            ("house_1", "ElectricityGridConnection", "grid_import"),
        ]

        assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)
        if grid_limit == 10:
            assert math.isclose(grid_flow.mean(), grid_limit, abs_tol=3e-3)
