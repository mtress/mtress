# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""
import math
import numpy as np

from test_core import (chp_revenue,
                       gas_costs_chp,
                       electricity_costs,
                       run_model_template,
                       HIGH_ACCURACY)


def test_electricity_demand_ap():
    electricity_demand = np.full(3, 0.1)

    params = {
        "demand": {"electricity": electricity_demand},
        "energy_cost": {"electricity": {"demand_rate": 0.5,
                                        "slp_price": 0}}}
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


def test_electricity_demand_lp():
    electricity_demand = np.full(3, 0.1)

    params = {
        "demand": {"electricity": electricity_demand},
        "energy_cost": {"electricity": {
            "demand_rate": 1000,
            "AP": 0}}}
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(
        meta_model.aggregate_flows(meta_model.demand_th_flows).sum(),
        0,
        abs_tol=1e-5)
    assert math.isclose(
        meta_model.aggregate_flows(meta_model.demand_el_flows).sum(),
        electricity_demand.sum())

    assert math.isclose(meta_model.operational_costs(),
                        electricity_costs(electricity_demand,
                                          params,
                                          meta_model.time_range))


def test_electricity_demand_all_costs():
    electricity_demand = np.full(3, 0.1)

    params = {
        "demand": {"electricity": electricity_demand},
        "energy_cost": {"electricity": {
            "demand_rate": 1000,
            "AP": [15, 20, 15]}}}
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(
        meta_model.aggregate_flows(meta_model.demand_th_flows).sum(),
        0,
        abs_tol=1e-5)
    assert math.isclose(
        meta_model.aggregate_flows(meta_model.demand_el_flows).sum(),
        electricity_demand.sum())

    assert math.isclose(meta_model.operational_costs(),
                        electricity_costs(electricity_demand,
                                          params,
                                          meta_model.time_range))


def test_chp():
    heat_demand = np.full(3, 2)
    gas_demand = 2*heat_demand
    electricity_production = heat_demand
    electricity_demand = np.array([0, 1, 0.5])
    electricity_export = electricity_production - electricity_demand

    params = {
        "chp": {"gas_input": 4,
                "thermal_output": 2,
                "electric_output": 2},
        "demand": {"heating": heat_demand,
                   "electricity": electricity_demand},
        "public_grid": False}
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(
        meta_model.aggregate_flows(meta_model.demand_th_flows).sum(),
        heat_demand.sum())
    assert math.isclose(
        meta_model.aggregate_flows(meta_model.chp_th_flows).sum(),
        heat_demand.sum(),
        rel_tol=1e-5)
    assert math.isclose(
        meta_model.aggregate_flows(meta_model.electricity_import_flows).sum(),
        0,
        abs_tol=HIGH_ACCURACY)
    assert math.isclose(
        meta_model.aggregate_flows(meta_model.electricity_export_flows).sum(),
        electricity_export.sum(),
        rel_tol=HIGH_ACCURACY)
    chp_export_flow = sum(meta_model.energy_system.results['main'][
                ("b_el_chp_fund", "b_elxprt")]['sequences']['flow'])
    assert math.isclose(chp_export_flow,
                        electricity_export.sum(),
                        rel_tol=HIGH_ACCURACY)
    optimiser_costs = meta_model.operational_costs()
    manual_costs = (gas_costs_chp(gas_demand, params)
                    - chp_revenue(electricity_export,
                                  electricity_demand.sum(),
                                  params))
    assert math.isclose(optimiser_costs,
                        manual_costs,
                        rel_tol=1e-5)


if __name__ == '__main__':
    test_chp()
