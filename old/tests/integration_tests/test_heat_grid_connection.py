import math
import pytest
from oemof.solph import Results
from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress.physics import HYDROGEN
from mtress.technologies import PEM_ELECTROLYSER


class TestHeatGrid:
    """
    This test covers:
    1) initialization of the technology
    2) heat import from an external source with a grid limit of 1e4 (W)
        and 10 (W)
    3) heat exchange between two locations with the same grid limits
    4) heat export to the grid
    """

    def test_grid_initialisation(self):
        grid_working_rate = None
        grid_revenue = None
        heat_network_temperature = 30
        flow_temperature = 30
        return_temperature = 10

        grid = technologies.HeatGridConnection(
            working_rate=grid_working_rate,
            revenue=grid_revenue,
            heat_network_temperature=heat_network_temperature,
            maximum_working_temperature=flow_temperature,
            minimum_working_temperature=return_temperature,
        )
        assert grid.working_rate == grid_working_rate
        assert grid.revenue == grid_revenue
        assert grid.maximum_working_temperature == flow_temperature
        assert grid.minimum_working_temperature == return_temperature

    @pytest.mark.skip(reason="Not really a unit test.")
    @pytest.mark.parametrize(
        "network_temperature, max_temperature, min_temperature, grid_limit, "
        "expected_result",
        [(30, 30, 20, 1e4, 400), (55, 55, 20, 10, 544.53)],
    )
    def test_heatgrid(
        self,
        network_temperature,
        max_temperature,
        min_temperature,
        grid_limit,
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
                heat_network_temperature=network_temperature,
                maximum_working_temperature=max_temperature,
                minimum_working_temperature=min_temperature,
                working_rate=10,
                grid_limit=grid_limit,
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
        mr = Results(solved_model)

        assert (
            solved_model.solver_results.Solver.Termination_condition
            == "optimal"
        )
        assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)

    @pytest.mark.skip(reason="Not really unit test.")
    @pytest.mark.parametrize(
        "network_temperature, max_temperature, min_temperature, grid_limit, "
        "expected_result",
        [(30, 30, 20, 1e4, 1200), (55, 55, 20, 20, 1778.12)],
    )
    def test_heatgrid_locations(
        self,
        network_temperature,
        max_temperature,
        min_temperature,
        grid_limit,
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
                heat_network_temperature=network_temperature,
                maximum_working_temperature=max_temperature,
                minimum_working_temperature=min_temperature,
                grid_limit=grid_limit,
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

        mr = Results(solved_model)

        assert (
            solved_model.solver_results.Solver.Termination_condition
            == "optimal"
        )
        assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)

    @pytest.mark.skip(reason="Not really a unit test.")
    @pytest.mark.parametrize(
        "temperature_network, max_temperature, min_temperature, revenue, "
        "grid_limit, expected_result",
        [
            (30, 55, 20, 10, 1e9, -746329.433),
            (30, 55, 20, 10, 1e3, -18151.21),
        ],
    )
    def test_heatgrid_export(
        self,
        temperature_network,
        max_temperature,
        min_temperature,
        revenue,
        grid_limit,
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
        house_1.add(
            carriers.GasCarrier(
                gases={
                    HYDROGEN: [30, 70],
                }
            )
        )
        house_1.add(technologies.ElectricityGridConnection(working_rate=0.0))
        house_1.add(
            technologies.HeatGridConnection(
                heat_network_temperature=temperature_network,
                maximum_working_temperature=max_temperature,
                minimum_working_temperature=min_temperature,
                grid_limit=grid_limit,
                revenue=revenue,
            )
        )
        house_1.add(
            technologies.Electrolyser(
                name="PEM_Ely",
                nominal_power=150e3,
                template=PEM_ELECTROLYSER,
                hydrogen_output_pressure=30,
            )
        )
        house_1.add(
            technologies.GasCompressor(
                name="H2Compr", nominal_power=50e3, gas_type=HYDROGEN
            )
        )
        house_1.add(
            demands.GasDemand(
                name="H2_demand",
                gas_type=HYDROGEN,
                time_series=[1, 1],
                pressure=70,
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

        mr = Results(solved_model)

        assert (
            solved_model.solver_results.Solver.Termination_condition
            == "optimal"
        )
        assert math.isclose(
            expected_result, float(mr["objective"]), abs_tol=3e-2
        )


if __name__ == "__main__":

    import os
    from oemof.solph import Results
    from mtress import (
        Location,
        MetaModel,
        SolphModel,
        carriers,
        demands,
        technologies,
    )

    from mtress.physics import HYDROGEN
    from mtress.technologies import PEM_ELECTROLYSER

    os.chdir(os.path.dirname(__file__))
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

    house_1.add(
        carriers.GasCarrier(
            gases={
                HYDROGEN: [30, 70],
            }
        )
    )
    house_1.add(technologies.ElectricityGridConnection(working_rate=0.0))

    house_1.add(
        technologies.HeatGridConnection(
            heat_network_temperature=30,
            maximum_working_temperature=55,
            minimum_working_temperature=20,
            grid_limit=1e9,
            revenue=10,
        )
    )

    house_1.add(
        technologies.Electrolyser(
            name="PEM_Ely",
            nominal_power=150e3,
            template=PEM_ELECTROLYSER,
            hydrogen_output_pressure=30,
        )
    )

    house_1.add(
        technologies.GasCompressor(
            name="H2Compr", nominal_power=50e3, gas_type=HYDROGEN
        )
    )

    house_1.add(
        demands.GasDemand(
            name="H2_demand",
            gas_type=HYDROGEN,
            time_series=[1, 1],
            pressure=70,
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

    mr = Results(solved_model)
    flows = mr["flow"]
    print("cost is: ", mr["objective"])
