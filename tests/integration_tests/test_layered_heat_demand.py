# -*- coding: utf-8 -*-
"""
Tests for MTRESS FixedTemperatureHeat Demand.
"""
import os

import numpy as np
from oemof import solph
import pytest

from mtress import carriers, Location, MetaModel, SolphModel
from mtress.demands import FixedTemperatureHeating as HeatDemand

@pytest.mark.skip(reason="Not adjusted to new HeatCarrier.")
def test_layered_heat_demand():
    house_1 = Location(name="house_1")
    house_1.add(
        carriers.HeatCarrier(
            temperature_levels=[0, 5, 10, 20, 30],
            reference_temperature=10,
        )
    )

    demand_levels =[
        (30, 20),
        (20, 0),
        (20, 10),
        (5, 0),
    ]
    demand_series = np.array([0, 2, 1, 0])
    for flow_temperature, return_temperature in demand_levels:
        house_1.add(HeatDemand(
            name=f"{flow_temperature}_{return_temperature}",
            min_flow_temperature=flow_temperature,
            return_temperature=return_temperature,
            time_series=demand_series,
        ))
    meta_model = MetaModel(locations=[house_1])

    solph_model = SolphModel(
        meta_model=meta_model,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 01:00:00",
            "freq": "15T",
        },
    )

    in_80 = list(solph_model.energy_system.nodes)[0]
    heat_source = solph.components.Source(
            label="heat_source",
            outputs={in_80: solph.Flow()}
    )
    solph_model.energy_system.add(heat_source)

    solph_model.build_solph_model()

    solph_model.solve()

    meta_results = solph.processing.meta_results(solph_model.model)
    results = solph.processing.results(solph_model.model)

    assert meta_results["solver"]["Termination condition"] == "optimal"
    supply_series = results[(heat_source, in_80)]["sequences"].squeeze()[:-1]

    assert (len(demand_levels) * demand_series == supply_series).all()

    return solph_model

if __name__ == "__main__":
    os.chdir(os.path.dirname (__file__))

    solph_model = test_layered_heat_demand()
    
    plot = solph_model.graph(detail=True)
    plot.render(outfile="layered_heat_demand.png")
