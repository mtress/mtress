# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""
import json
import os
import math
import numpy as np
import pandas as pd

from oemof.solph import views, processing

from mtress import MetaModel

HIGH_ACCURACY = 1e-5
OKAY_ACCURACY = 1e-5  # sometimes, 2.5 % are good enough


def run_model_template(custom_params=None):
    if custom_params is None:
        custom_params = {}

    dir_name = os.path.dirname(__file__)
    filename = os.path.join(dir_name, "empty_template.json")
    with open(filename) as f:
        params = json.load(f)

    for key1 in custom_params:
        if key1 not in params:
            params[key1] = custom_params[key1]
        else:
            for key2 in custom_params[key1]:
                if type(custom_params[key1][key2]) == dict:
                    for key3 in custom_params[key1][key2]:
                        params[key1][key2][key3] = (
                            custom_params[key1][key2][key3])
                else:
                    params[key1][key2] = custom_params[key1][key2]

    params["demand"] = pd.DataFrame(
        params["demand"],
        index=pd.date_range('1/1/2000', periods=3, freq='H'))
    meta_model = MetaModel(**params)

    meta_model.model.solve(solver="cbc",
                           solve_kwargs={'tee': False},
                           solver_io='lp',
                           cmdline_options={'ratio': 0.01})

    meta_model.energy_system.results['main'] = views.convert_keys_to_strings(
        processing.results(meta_model.model))
    meta_model.energy_system.results['meta'] = processing.meta_results(
        meta_model.model)

    return meta_model, params


def electricity_costs(electricity_demand, params, time_range):
    working_price = sum(electricity_demand
                        * (np.array(params["energy_cost"][
                                       "electricity"]["market"])
                           + params["energy_cost"][
                                       "electricity"]["surcharge"]))
    demand_rate = (max(electricity_demand) * time_range
                   * params["energy_cost"]["electricity"]["demand_rate"])
    return working_price + demand_rate


def gas_costs(gas_demand, params):
    return sum(gas_demand * np.array(params["energy_cost"]['gas']["fossil_gas"]))


def gas_costs_chp(gas_demand, params):
    return gas_costs(gas_demand, params) - \
           sum(gas_demand * np.array(params["energy_cost"]['gas']["energy_tax"]))


def chp_revenue(export, own_consumption, params):
    # TODO: Consider funding hours per year
    feed_in_revenue = (export * (params["energy_cost"]["electricity"]["market"]
                       + params["chp"]["feed_in_subsidy"])).sum()
    oc_costs = own_consumption * (params["energy_cost"]['electricity']['eeg_levy']
                                  - params["chp"]["own_consumption_subsidy"])
    return feed_in_revenue - oc_costs


def test_empty_template():
    meta_model, params = run_model_template()

    thermal_demand = meta_model.aggregate_flows(meta_model.demand_th_flows).sum()
    el_demand = meta_model.aggregate_flows(meta_model.demand_el_flows).sum()
    el_generation = meta_model.aggregate_flows(meta_model.production_el_flows).sum()

    assert math.isclose(thermal_demand, 0, abs_tol=HIGH_ACCURACY)
    assert math.isclose(el_demand, 0, abs_tol=HIGH_ACCURACY)
    assert math.isclose(el_generation, 0, abs_tol=HIGH_ACCURACY)
    assert math.isclose(meta_model.operational_costs(), 0, abs_tol=HIGH_ACCURACY)


def test_missing_heat():
    heat_demand = 0.3

    params = {
        "demand": {"heating": 3 * [heat_demand / 3]},
        "allow_missing_heat": True
    }
    meta_model, params = run_model_template(custom_params=params)

    thermal_demand = meta_model.aggregate_flows(meta_model.demand_th_flows).sum()
    missing_heat = meta_model.aggregate_flows(meta_model.missing_heat_flow).sum()

    assert math.isclose(thermal_demand, heat_demand)
    assert math.isclose(missing_heat, heat_demand,
                        rel_tol=HIGH_ACCURACY)
