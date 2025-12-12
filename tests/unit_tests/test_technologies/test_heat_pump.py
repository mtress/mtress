import math
import pytest
from oemof.solph import Results

from mtress.technologies import HeatPump, COPReference
from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)


def test_heat_pump_initialisation():
    hp_name = "test_hp"
    hp_thermal_power_limit = 5e3  # W
    hp_ref_cop = COPReference(4.6)

    hp = HeatPump(
        name=hp_name,
        thermal_power_limit=hp_thermal_power_limit,
        ref_cop=hp_ref_cop,
    )

    assert hp.name == hp_name
    assert hp.thermal_power_limit == hp_thermal_power_limit
    assert hp.ref_cop == hp_ref_cop


def test_heat_pump_init_custom_design_conditions():
    hp_name = "test_hp"
    hp_thermal_power_limit = 4e3  # W
    hp_ref_cop = COPReference(3.6, 5, -10, 40, 25)

    hp = HeatPump(
        name=hp_name,
        thermal_power_limit=hp_thermal_power_limit,
        ref_cop=hp_ref_cop,
    )

    assert hp.name == hp_name
    assert hp.thermal_power_limit == hp_thermal_power_limit
    assert hp.ref_cop == hp_ref_cop


@pytest.mark.skip(reason="Not really unit test.")
def test_heat_pump_heating_example():

    energy_system = MetaModel()

    house_1 = Location(name="house_1")
    energy_system.add_location(house_1)

    # Add carrier
    house_1.add(carriers.ElectricityCarrier())
    house_1.add(technologies.ElectricityGridConnection(working_rate=35))

    house_1.add(
        carriers.HeatCarrier(
            temperature_levels=[10, 15, 20, 30, 40, 55],
        )
    )

    # Add technologies
    house_1.add(
        technologies.HeatSource(
            name="Air_HE",
            reservoir_temperature=20,
            maximum_working_temperature=40,
            minimum_working_temperature=10,
            nominal_power=1e4,
        )
    )

    house_1.add(
        technologies.HeatPump(
            name="HeatPump",
            thermal_power_limit=None,
            max_temp_primary=20,
            min_temp_primary=10,
            max_temp_secondary=40,
            min_temp_secondary=30,
        )
    )

    house_1.add(
        demands.FixedTemperatureHeating(
            name="Heating_demand",
            min_flow_temperature=40,
            return_temperature=30,
            time_series=[50, 50, 30, 40],
        )
    )

    solph_representation = SolphModel(
        energy_system,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 04:00:00",
            "freq": "60min",
        },
    )

    solph_representation.build_solph_model()

    solved_model = solph_representation.solve(solve_kwargs={"tee": True})
    mr = Results(solved_model)

    pyomo_objective = 640.7893695

    assert math.isclose(pyomo_objective, mr["objective"], abs_tol=3e-3)
