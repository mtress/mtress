# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""
import math
import numpy as np

from test_core import (electricity_costs,
                       run_model_template,
                       HIGH_ACCURACY)


def test_demand_only_exclusive():
    electricity_demand = np.full(3, 0.1)

    params = {
        "demand": {"electricity": electricity_demand},
        "energy_cost": {"electricity": {"demand_rate": 0.5}},
        "exclusive_grid_connection": True}
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(
        meta_model.aggregate_flows(meta_model.demand_th_flows).sum(),
        0,
        abs_tol=1e-5)
    assert math.isclose(
        meta_model.aggregate_flows(meta_model.demand_el_flows).sum(),
        electricity_demand.sum(),
        abs_tol=1e-5)

    assert math.isclose(meta_model.operational_costs(),
                        electricity_costs(electricity_demand,
                                          params,
                                          meta_model.time_range))


def test_demand_only_non_exclusive():
    electricity_demand = np.full(3, 0.1)

    params = {
        "demand": {"electricity": electricity_demand},
        "energy_cost": {"electricity": {"demand_rate": 0.5}},
        "exclusive_grid_connection": False}
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(
        meta_model.aggregate_flows(meta_model.demand_el_flows).sum(),
        electricity_demand.sum(),
        abs_tol=HIGH_ACCURACY)

    assert math.isclose(meta_model.operational_costs(),
                        electricity_costs(electricity_demand,
                                          params,
                                          meta_model.time_range))


def test_demand_supply_exclusive():
    electricity_demand = np.full(3, 0.1)
    electricity_generation = np.array([0.1, 0.5, 0])
    electricity_balance = electricity_generation - electricity_demand
    electricity_import = -electricity_balance
    electricity_import[electricity_import < 0] = 0
    electricity_export = electricity_balance
    electricity_export[electricity_export < 0] = 0

    feed_in_subsidy = 1
    el_market_price = feed_in_subsidy/2

    params = {
        "demand": {"electricity": electricity_demand},
        "energy_cost": {"electricity": {"market": el_market_price}},
        "pv": {
            "nominal_power": 1,
            "feed_in_subsidy": feed_in_subsidy,
            "spec_generation": electricity_generation
        },
        "exclusive_grid_connection": True
    }
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(
        meta_model.aggregate_flows(meta_model.demand_el_flows).sum(),
        electricity_demand.sum(),
        abs_tol=HIGH_ACCURACY)

    assert math.isclose(
        meta_model.aggregate_flows(meta_model.grid_el_flows).sum(),
        electricity_import.sum(),
        abs_tol=HIGH_ACCURACY)

    op_costs = meta_model.operational_costs()
    assert math.isclose(meta_model.operational_costs(),
                        electricity_costs(electricity_import,
                                          params,
                                          meta_model.time_range)
                        - electricity_export.sum() * feed_in_subsidy)


def test_demand_supply_non_exclusive():
    electricity_demand = np.full(3, 0.1)
    electricity_generation = np.array([0.1, 0.5, 0])
    electricity_balance = electricity_generation - electricity_demand
    electricity_import = -electricity_balance
    electricity_import[electricity_import < 0] = 0
    electricity_export = electricity_balance
    electricity_export[electricity_export < 0] = 0

    feed_in_subsidy = 1
    el_market_price = feed_in_subsidy/2

    params = {
        "demand": {"electricity": electricity_demand},
        "energy_cost": {"electricity": {"market": el_market_price}},
        "pv": {
            "nominal_power": 1,
            "feed_in_subsidy": feed_in_subsidy,
            "spec_generation": electricity_generation
        },
        "exclusive_grid_connection": False
    }
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(
        meta_model.aggregate_flows(meta_model.demand_el_flows).sum(),
        electricity_demand.sum(),
        abs_tol=HIGH_ACCURACY)

    assert math.isclose(
        meta_model.aggregate_flows(meta_model.grid_el_flows).sum(),
        electricity_demand.sum(),
        abs_tol=HIGH_ACCURACY)

    op_costs = meta_model.operational_costs()  # -0.35
    el_costs = electricity_costs(electricity_import,
                                          params,
                                          meta_model.time_range)
    el_revenue = electricity_export.sum() * feed_in_subsidy
    assert math.isclose(op_costs, el_costs - el_revenue)


if __name__ == '__main__':
    test_demand_supply_non_exclusive()
