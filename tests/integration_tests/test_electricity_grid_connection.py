from mtress.technologies import ElectricityGridConnection
from oemof.solph import Results
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


class TestGridConnection:
    """
    1. Test the initialisation
    2. Test a constraint on the import of the grid:
        a) A limit of 10 W is specified. Expected result: 300
            import = 20*10 = 200
            penalty = 1*100 = 100
        b) No limit is specified. Expected result: 210
    """

    def test_grid_initialisation(self):
        grid_working_rate = None
        grid_demand_rate = None
        grid_import_limit = None
        grid_export_limit = None

        grid = ElectricityGridConnection(
            working_rate=grid_working_rate,
            demand_rate=grid_demand_rate,
            grid_import_limit=grid_import_limit,
            grid_export_limit=grid_export_limit,
        )

        assert grid.working_rate == grid_working_rate
        assert grid.demand_rate == grid_demand_rate
        assert grid.grid_import_limit == grid_import_limit
        assert grid.grid_export_limit == grid_export_limit

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

        solved_model = solph_representation.solve(solve_kwargs={"tee": False})
        mr = Results(solved_model)
        flows = mr["flow"]

        label1 = ("source_import", "ElectricityGridConnection", "house_1")
        label2 = ("grid_import", "ElectricityGridConnection", "house_1")
        grid_flow = (str(label1), str(label2))

        assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)
        if grid_limit is not None:
            assert math.isclose(
                flows[grid_flow].iloc[0], grid_limit, abs_tol=3e-3
            )


class TestGridExport:
    """
    This test limits the grid's exports to 5 W. So, only 10 W in total can be
    exported and the rest will be sent to the slack with a penalty of 10
    (currency) per unit of electricity.
    Expected result: 900
        penalty = 10*100 = 1000
        revenue = 10*10 = 100
    """

    @pytest.mark.parametrize(
        "export_limit, expected_result",
        [(5, 900.0), (None, -200)],
    )
    def test_grid_exports_example(self, export_limit, expected_result):

        energy_system = MetaModel()

        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(
            technologies.ElectricityGridConnection(
                working_rate=10, revenue=10, grid_export_limit=export_limit
            )
        )
        house_1.add(
            technologies.RenewableElectricitySource(
                name="Wind_Park",
                nominal_power=1,
                specific_generation=[10, 10],
                working_rate=0,
                fixed=True,
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
        solved_model = solph_representation.solve(solve_kwargs={"tee": False})
        mr = Results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)
