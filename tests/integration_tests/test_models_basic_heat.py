# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""
import math
import numpy as np

from test_core import (electricity_costs,
                       gas_costs,
                       run_model_template,
                       HIGH_ACCURACY)


def test_gas_boiler():
    heat_demand = np.full(3, 0.1)

    params = {
        "gas_boiler": {"thermal_output": 1},
        "demand": {"heating": {"values": heat_demand,
                               "flow_temperature": 40,
                               "return_temperature": 30}}
    }
    meta_model, params = run_model_template(custom_params=params)

    thermal_demand = meta_model.aggregate_flows(meta_model.demand_th_flows).sum()
    el_demand = meta_model.aggregate_flows(meta_model.demand_el_flows).sum()

    boiler_generation = meta_model.aggregate_flows(meta_model.boiler_th_flows).sum()
    p2h_generation = meta_model.aggregate_flows(meta_model.p2h_th_flows).sum()

    assert math.isclose(thermal_demand, heat_demand.sum())
    assert math.isclose(boiler_generation, heat_demand.sum(),
                        rel_tol=HIGH_ACCURACY)
    assert math.isclose(p2h_generation, 0, rel_tol=HIGH_ACCURACY)
    assert math.isclose(el_demand, 0, rel_tol=HIGH_ACCURACY)

    assert math.isclose(meta_model.operational_costs(),
                        gas_costs(heat_demand, params))


def test_missing_heat():
    heat_demand = 0.3

    params = {
        "demand": {
            "heating": {
                "values": 3 * [heat_demand/3],
                "flow_temperature": 35,
                "return_temperature": 30}
        },
        "allow_missing_heat": True
    }
    meta_model, params = run_model_template(custom_params=params)

    thermal_demand = meta_model.aggregate_flows(meta_model.demand_th_flows).sum()
    missing_heat = meta_model.aggregate_flows(meta_model.missing_heat_flow).sum()

    assert math.isclose(thermal_demand, heat_demand)
    assert math.isclose(missing_heat, heat_demand,
                        rel_tol=HIGH_ACCURACY)
