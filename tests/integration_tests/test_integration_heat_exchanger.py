# -*- coding: utf-8 -*-
"""
Tests for MTRESS HeatExchanger
"""
import os

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


def test_solar_collector():
    energy_system = MetaModel()

    house_1 = Location(name="house_1")
    energy_system.add_location(house_1)

    house_1.add(
        carriers.HeatCarrier(
            temperature_levels=[10, 15, 25, 30, 45],
        )
    )

    house_1.add(
        technologies.HeatSource(
            name="thColl",
            reservoir_temperature=[15, 25],
            maximum_working_temperature=45,
            minimum_working_temperature=10,
            nominal_power=10,
        )
    )

    house_1.add(
        technologies.HeatSink(
            name="HeatSink",
            reservoir_temperature=[0, 0],
            maximum_working_temperature=45,
            minimum_working_temperature=0,
            nominal_power=50,
            revenue=42,
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

    return solph_representation, myresults


if __name__ == "__main__":
    model, myresults = test_solar_collector()

    flows = get_flows(myresults)
    model.graph(
        flow_results=flows,
        path="results.png",
    )
