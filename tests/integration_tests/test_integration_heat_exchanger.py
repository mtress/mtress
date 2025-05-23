# -*- coding: utf-8 -*-
"""
Tests for MTRESS HeatExchanger
"""
import os

import numpy as np
import pytest
from oemof.solph.processing import results

from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress._helpers import get_flows


def _heat_source_test_template(
    reservoir_temperature,
    temperature_levels,
    results1=None,
    results2=None,
    results3=None,
    nominal_power=10,
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
            name="HeatSink1",
            reservoir_temperature=[0, 0],
            maximum_working_temperature=20,
            minimum_working_temperature=10,
            nominal_power=500,
            revenue=42,
        )
    )

    house_1.add(
        technologies.HeatSink(
            name="HeatSink2",
            reservoir_temperature=[0, 0],
            maximum_working_temperature=25,
            minimum_working_temperature=20,
            nominal_power=500,
            revenue=120,
        )
    )

    house_1.add(
        technologies.HeatSink(
            name="HeatSink3",
            reservoir_temperature=[0, 0],
            maximum_working_temperature=30,
            minimum_working_temperature=25,
            nominal_power=500,
            revenue=125,
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

    myresults = results(solved_model)

    flows = get_flows(myresults)

    flow1 = flows[
        ("house_1", "HeatSink1", "output"),
        ("house_1", "HeatSink1", "sink"),
    ]
    flow2 = flows[
        ("house_1", "HeatSink2", "output"),
        ("house_1", "HeatSink2", "sink"),
    ]
    flow3 = flows[
        ("house_1", "HeatSink3", "output"),
        ("house_1", "HeatSink3", "sink"),
    ]

    if results1 is not None:
        # lower temperature and revenue, allowed in both step
        assert flow1.iloc[0] == pytest.approx(results1[0])
        assert flow1.iloc[1] == pytest.approx(results1[1])
    else:
        print(flow1)

    if results2 is not None:
        # higher temperature and revenue, only allowed in second step
        assert flow2.iloc[0] == pytest.approx(results2[0])
        assert flow2.iloc[1] == pytest.approx(results2[1])
    else:
        print(flow2)

    if results3 is not None:
        # higherst temperature and revenue, not allowed at all
        assert flow3.iloc[0] == pytest.approx(results3[0])
        assert flow3.iloc[1] == pytest.approx(results3[1])
    else:
        print(flow3)

    return solph_representation, myresults


def test_heat_source():
    _heat_source_test_template(
        reservoir_temperature=[21, 30],
        temperature_levels=[10, 20, 25, 30],
        results1=[10, 0],
        results2=[0, 10],
        results3=[0, 0],
    )
    _heat_source_test_template(
        reservoir_temperature=[21, 31],
        temperature_levels=[10, 20, 25, 30],
        results1=[10, 0],
        results2=[0, 0],
        results3=[0, 10],
    )
    _heat_source_test_template(
        reservoir_temperature=[21, 30],
        conductivity_gain_factor=0.8,
        temperature_levels=[10, 20, 25, 30],
        results1=[0.8, 6],
        results2=[0, 4],
        results3=[0, 0],
    )


if __name__ == "__main__":
    model, myresults = _heat_source_test_template(
        nominal_power=10,
        reservoir_temperature=[21, 30],
        conductivity_gain_factor=0.5,
        temperature_levels=[10, 20, 25, 30],
        non_thermal_gains=0.1,
        #results1=[0.8, 6],
        #results2=[0, 4],
        #results3=[0, 0],
    )

    flows = get_flows(myresults)
    model.graph(
        flow_results=flows,
        path="results.png",
    )
