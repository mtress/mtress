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
        "demand": {"heating": heat_demand}}
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


def test_booster():
    dhw_demand = np.full(3, 0.1)
    electricity_demand = 1 / 3 * dhw_demand
    gas_demand = 2 / 3 * dhw_demand

    params = {
        "gas_boiler": {"thermal_output": 1},
        "demand": {
            "dhw": dhw_demand}}
    meta_model, params = run_model_template(custom_params=params)

    thermal_demand = meta_model.aggregate_flows(meta_model.demand_th_flows).sum()
    el_demand = meta_model.aggregate_flows(meta_model.demand_el_flows).sum()

    boiler_generation = meta_model.aggregate_flows(meta_model.boiler_th_flows).sum()
    p2h_consumption = meta_model.aggregate_flows(meta_model.p2h_el_flows).sum()
    p2h_generation = meta_model.aggregate_flows(meta_model.p2h_th_flows).sum()

    assert math.isclose(thermal_demand, dhw_demand.sum())
    assert math.isclose(boiler_generation.sum(), gas_demand.sum(),
                        rel_tol=HIGH_ACCURACY)
    assert math.isclose(p2h_generation.sum() + boiler_generation.sum(),
                        thermal_demand.sum(),
                        rel_tol=HIGH_ACCURACY)
    assert math.isclose(p2h_consumption, electricity_demand.sum(),
                        rel_tol=HIGH_ACCURACY)
    assert math.isclose(el_demand, electricity_demand.sum(),
                        rel_tol=HIGH_ACCURACY)

    assert math.isclose(meta_model.operational_costs(),
                        electricity_costs(electricity_demand,
                                          params,
                                          meta_model.time_range)
                        + gas_costs(gas_demand, params),
                        rel_tol=HIGH_ACCURACY)


def test_booster_heat_drop():
    dhw_demand = np.full(3, 0.1)
    electricity_demand = 0.5 * dhw_demand
    gas_demand = 0.5 * dhw_demand

    params = {
        "gas_boiler": {"thermal_output": 1},
        "demand": {"dhw": dhw_demand},
        "temperatures": {"heat_drop_exchanger_dhw": 10}}  # +50% for booster
    meta_model, params = run_model_template(custom_params=params)

    thermal_demand = meta_model.aggregate_flows(meta_model.demand_th_flows).sum()
    el_demand = meta_model.aggregate_flows(meta_model.demand_el_flows).sum()

    boiler_generation = meta_model.aggregate_flows(meta_model.boiler_th_flows).sum()
    p2h_consumption = meta_model.aggregate_flows(meta_model.p2h_el_flows).sum()
    p2h_generation = meta_model.aggregate_flows(meta_model.p2h_th_flows).sum()

    assert math.isclose(thermal_demand, dhw_demand.sum())
    assert math.isclose(boiler_generation, gas_demand.sum(),
                        rel_tol=HIGH_ACCURACY)
    assert math.isclose(p2h_generation.sum() + boiler_generation.sum(),
                        dhw_demand.sum(),
                        rel_tol=HIGH_ACCURACY)
    assert math.isclose(p2h_consumption, electricity_demand.sum(),
                        rel_tol=HIGH_ACCURACY)
    assert math.isclose(el_demand, electricity_demand.sum(),
                        rel_tol=HIGH_ACCURACY)

    assert math.isclose(meta_model.operational_costs(),
                        electricity_costs(electricity_demand,
                                          params,
                                          meta_model.time_range)
                        + gas_costs(gas_demand, params),
                        rel_tol=HIGH_ACCURACY)
