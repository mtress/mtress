# -*- coding: utf-8 -*-
"""
Tests for MTRESS HeatExchanger
"""
import pandas as pd
import math

from oemof.solph import Results
from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    technologies,
)


def _heat_source_test_template(
    reservoir_temperature,
    temperature_levels,
    results_20_10=None,
    results_25_20=None,
    results_30_25=None,
    nominal_power=10,
    power_per_sink=10,
    conductivity_gain_factor=None,
    non_thermal_gains=0,
):
    energy_system = MetaModel()

    house_1 = Location(name="house_1")
    energy_system.add_location(house_1)

    house_1.add(
        carriers.HeatCarrier(
            temperature_levels=temperature_levels,
        )
    )

    house_1.add(
        technologies.HeatSource(
            name="thColl",
            reservoir_temperature=reservoir_temperature,
            maximum_working_temperature=45,
            minimum_working_temperature=10,
            nominal_power=nominal_power,
            conductivity_gain_factor=conductivity_gain_factor,
            non_thermal_gains=non_thermal_gains,
        )
    )

    house_1.add(
        technologies.HeatSink(
            name="HeatSink_20_10",
            reservoir_temperature=[0, 0],
            maximum_working_temperature=20,
            minimum_working_temperature=10,
            nominal_power=power_per_sink,
            revenue=1,
        )
    )

    house_1.add(
        technologies.HeatSink(
            name="HeatSink_25_20",
            reservoir_temperature=[0, 0],
            maximum_working_temperature=25,
            minimum_working_temperature=20,
            nominal_power=power_per_sink,
            revenue=5,
        )
    )

    house_1.add(
        technologies.HeatSink(
            name="HeatSink_30_25",
            reservoir_temperature=[0, 0],
            maximum_working_temperature=30,
            minimum_working_temperature=25,
            nominal_power=power_per_sink,
            revenue=25,
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

    solved_model = solph_representation.solve(solve_kwargs={"tee": False})

    myresults = Results(solved_model)
    flows = myresults["flow"]

    label1 = ("output", "HeatSink_20_10", "house_1")
    label2 = ("sink", "HeatSink_20_10", "house_1")
    flow_20_10 = flows[str(label1), str(label2)]

    label1 = ("output", "HeatSink_25_20", "house_1")
    label2 = ("sink", "HeatSink_25_20", "house_1")
    flow_25_20 = flows[str(label1), str(label2)]

    label1 = ("output", "HeatSink_30_25", "house_1")
    label2 = ("sink", "HeatSink_30_25", "house_1")
    flow_30_25 = flows[str(label1), str(label2)]

    if results_20_10 is not None:
        # lower temperature and revenue, allowed in both step
        assert math.isclose(flow_20_10.iloc[0], results_20_10[0], abs_tol=1e-3)
        assert math.isclose(flow_20_10.iloc[1], results_20_10[1], abs_tol=1e-3)
    else:
        print(flow_20_10)

    if results_25_20 is not None:
        # higher temperature and revenue, only allowed in second step
        assert math.isclose(flow_25_20.iloc[0], results_25_20[0], abs_tol=1e-3)
        assert math.isclose(flow_25_20.iloc[1], results_25_20[1], abs_tol=1e-3)
    else:
        print(flow_25_20)

    if results_30_25 is not None:
        # higherst temperature and revenue, not allowed at all
        assert math.isclose(flow_30_25.iloc[0], results_30_25[0], abs_tol=1e-3)
        assert math.isclose(flow_30_25.iloc[1], results_30_25[1], abs_tol=1e-3)
    else:
        print(flow_30_25)

    return solph_representation, myresults


def test_heat_source_1():
    _heat_source_test_template(
        reservoir_temperature=[21, 29.99],
        temperature_levels=[10, 20, 25, 30],
        results_20_10=[10, 0],
        results_25_20=[0, 10],
        results_30_25=[0, 0],
    )


def test_heat_source_2():
    _heat_source_test_template(
        reservoir_temperature=[21, 30],
        temperature_levels=[10, 20, 25, 30],
        results_20_10=[10, 0],
        results_25_20=[0, 0],
        results_30_25=[0, 10],
    )


def test_heat_source_3():
    _heat_source_test_template(
        reservoir_temperature=[21, 29],
        conductivity_gain_factor=0.8,
        temperature_levels=[10, 20, 25, 30],
        results_20_10=[8, 0],  # 8 = 0.8 * (21 - 20) * 10
        results_25_20=[0, 10],
        results_30_25=[0, 0],
    )


def test_heat_source_4():
    _heat_source_test_template(
        reservoir_temperature=[21, 30],
        conductivity_gain_factor=0.8,
        temperature_levels=[10, 15, 20, 25, 30],
        results_20_10=[10, 0],  # new level allows gains at 15 °C
        results_25_20=[0, 10],
        results_30_25=[0, 0],
    )


def test_heat_source_5():
    _heat_source_test_template(
        nominal_power=10,
        reservoir_temperature=[21, 30],
        conductivity_gain_factor=0.8,
        temperature_levels=[10, 20, 25, 30],
        non_thermal_gains=0.1,
        results_20_10=[9, 0],  # 9 = (0.8 * (21 - 20) + 0.1) * 10
        results_25_20=[0, 10],  # more profitable than 1 at higher level
        results_30_25=[0, 0],  # <= 1 = (0.8 * (30 - 30) + 0.1) * 10
    )


def test_heat_source_6():
    _heat_source_test_template(
        nominal_power=10,
        reservoir_temperature=[21, 30],
        conductivity_gain_factor=0.1,
        temperature_levels=[10, 20, 25, 30],
        non_thermal_gains=0.9,
        results_20_10=[0, 0],
        results_25_20=[5, 0],  # 5 = (0.1 * (21 - 25) + 0.9) * 10
        results_30_25=[0, 9],  # 9 = (0.1 * (30 - 30) + 0.9) * 10
    )


def test_heat_source_7():
    _heat_source_test_template(
        nominal_power=20,
        power_per_sink=10,
        reservoir_temperature=[21, 30],
        conductivity_gain_factor=0.1,
        temperature_levels=[10, 20, 25, 30],
        non_thermal_gains=0.9,
        results_20_10=[0, 0],
        results_30_25=[0, 10],  # sink limit uses 10/18 = 5/9 of capacity
        results_25_20=[10, 80 / 9],  # remaining 4/9 of 20 W
    )


if __name__ == "__main__":

    test_heat_source_1()
