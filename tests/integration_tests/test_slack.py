from mtress.technologies import SlackNode
from mtress import MetaModel, Location, SolphModel, carriers, demands
from mtress import technologies
from mtress.physics import HYDROGEN
from oemof.solph import Results
import math
import pytest


class TestSlack:

    # tests:
    # 1) penalty for all
    # 2) multiple carriers with different penalties
    # 3) penalties apply only to carriers specified or to all

    @pytest.mark.parametrize(
        "penalty, grid_limit, expected_result",
        [
            (100, 10, 300.0),
            (100, None, 210.0),
            (200, 10, 400.0),  # int
            (200.0, 10, 400.0),  # float
            (200, None, 210.0),
        ],
    )
    def test_simple(self, penalty, grid_limit, expected_result):
        # test inspired on test_grid_imports_example originally found in
        # test_electricity_grid_connection.py

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
        house_1.add(technologies.SlackNode(penalty=penalty))
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

    @pytest.mark.parametrize(
        "penalties, expected_result",
        # penalties for each carrier
        [
            (
                {
                    carriers.ElectricityCarrier: 1000,
                    carriers.HeatCarrier: 1e5,
                    carriers.GasCarrier: 1e7,
                },
                30106359.1728,
            ),
            # different penalties for each carrier
            (
                {
                    carriers.ElectricityCarrier: 2000,
                    carriers.HeatCarrier: 1e4,
                    carriers.GasCarrier: 0.5 * 1e7,
                },
                15016335.91728,
            ),
            # same penalty for all
            (
                {
                    carriers.ElectricityCarrier: 100000,
                    # = 1e5 as integer literal
                    carriers.HeatCarrier: 1e5,
                    carriers.GasCarrier: 1e5,
                },
                703359.1728000001,
            ),
            # same penalty for all without using a dict
            (1e5, 703359.1728000001),
            # penalties for all but one carrier -> no alternative -> infeasible
            (
                {
                    carriers.ElectricityCarrier: 2000,
                    carriers.HeatCarrier: 1e4,
                    # carriers.GasCarrier: 0.5*1e7, # omit to trigger
                    # infeasibility
                },
                None,
            ),
        ],
    )
    def test_multiple_carriers(self, penalties, expected_result):

        meta_model = MetaModel()
        location = Location(name="location")
        meta_model.add_location(location)

        location.add(carriers.ElectricityCarrier())
        location.add(
            demands.Electricity(
                name="electricity_demand", time_series=[0, 1, 2]
            )
        )

        location.add(
            carriers.HeatCarrier(
                temperature_levels=[10, 20],
            )
        )
        location.add(
            demands.FixedTemperatureHeating(
                name="heat_demand",
                min_flow_temperature=20,
                return_temperature=10,
                time_series=[1, 2, 3],
            )
        )

        location.add(carriers.GasCarrier(gases={HYDROGEN: [30]}))
        location.add(
            demands.GasDemand(
                name="H2_demand",
                gas_type=HYDROGEN,
                time_series=[0.5, 1.0, 1.5],
                pressure=30,
            )
        )

        location.add(SlackNode(penalties))

        solph_representation = SolphModel(
            meta_model,
            timeindex={
                "start": "2021-07-10 00:00:00",
                "end": "2021-07-10 03:00:00",
                "freq": "60T",
            },
        )
        solph_representation.build_solph_model()

        if expected_result is None:
            with pytest.raises(Exception):
                solved_model = solph_representation.solve(
                    solve_kwargs={"tee": False}
                )
                mr = Results(solved_model)

        else:
            solved_model = solph_representation.solve(
                solve_kwargs={"tee": False}
            )
            mr = Results(solved_model)
            assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)
