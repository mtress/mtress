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
                       HIGH_ACCURACY,
                       OKAY_ACCURACY)


def test_heat_pump_r0_b0():
    heat_demand = np.full(3, 0.1)
    design_cop = 5
    electricity_demand = heat_demand / design_cop

    params = {
        "heat_pump": {"electric_input": 1,
                      "cop_0_35": design_cop},
        "geothermal_heat_source": {"thermal_output": 1},
        "demand": {
            "heating": heat_demand},
        "temperatures": {"reference": 0,
                         "forward_flow": 35,
                         "backward_flow": 0}}
    meta_model, params = run_model_template(custom_params=params)

    thermal_demand = meta_model.aggregate_flows(
        meta_model.th_demand_flows).sum()
    bhp_generation = meta_model.aggregate_flows(meta_model.hp_flows).sum()

    el_import = meta_model.aggregate_flows(meta_model.el_import_flows).sum()

    assert math.isclose(thermal_demand, heat_demand.sum())
    assert math.isclose(bhp_generation, heat_demand.sum(),
                        rel_tol=HIGH_ACCURACY)
    design_cop_heat = el_import * design_cop
    assert math.isclose(design_cop_heat,
                        heat_demand.sum(),
                        rel_tol=OKAY_ACCURACY)
    assert math.isclose(meta_model.operational_costs(),
                        electricity_costs(electricity_demand,
                                          params,
                                          meta_model.time_range),
                        rel_tol=OKAY_ACCURACY)


def test_heat_pump_r0_b30():
    heat_demand = np.full(3, 0.1)
    design_cop = 5
    electricity_demand = heat_demand/design_cop

    params = {
        "heat_pump": {"electric_input": 1,
                      "cop_0_35": design_cop},
        "geothermal_heat_source": {"thermal_output": 1},
        "demand": {
            "heating": heat_demand},
        "temperatures": {"reference": 0,
                         "forward_flow": 35,
                         "backward_flow": 30}}
    meta_model, params = run_model_template(custom_params=params)

    thermal_demand = meta_model.aggregate_flows(
        meta_model.th_demand_flows).sum()
    bhp_generation = meta_model.aggregate_flows(meta_model.hp_flows).sum()

    el_import = meta_model.aggregate_flows(meta_model.el_import_flows).sum()

    assert math.isclose(thermal_demand, heat_demand.sum())
    assert math.isclose(bhp_generation, heat_demand.sum(),
                        rel_tol=HIGH_ACCURACY)
    design_cop_heat = el_import * design_cop
    assert math.isclose(design_cop_heat,
                        heat_demand.sum(),
                        rel_tol=OKAY_ACCURACY)
    assert math.isclose(meta_model.operational_costs(),
                        electricity_costs(electricity_demand,
                                          params,
                                          meta_model.time_range),
                        rel_tol=OKAY_ACCURACY)


def test_heat_pump_r30_b30():
    heat_demand = np.full(3, 0.1)
    design_cop = 5
    electricity_demand = heat_demand/design_cop

    params = {
        "heat_pump": {"electric_input": 1,
                      "cop_0_35": design_cop},
        "geothermal_heat_source": {"thermal_output": 1},
        "demand": {
            "heating": heat_demand},
        "temperatures": {"reference": 30,
                         "forward_flow": 35,
                         "backward_flow": 30}}
    meta_model, params = run_model_template(custom_params=params)

    thermal_demand = meta_model.aggregate_flows(
        meta_model.th_demand_flows).sum()
    bhp_generation = meta_model.aggregate_flows(meta_model.hp_flows).sum()

    el_import = meta_model.aggregate_flows(meta_model.el_import_flows).sum()

    assert math.isclose(thermal_demand, heat_demand.sum())
    assert math.isclose(bhp_generation, heat_demand.sum(),
                        rel_tol=HIGH_ACCURACY)
    design_cop_heat = el_import * design_cop
    assert math.isclose(design_cop_heat,
                        heat_demand.sum(),
                        rel_tol=OKAY_ACCURACY)
    assert math.isclose(meta_model.operational_costs(),
                        electricity_costs(electricity_demand,
                                          params,
                                          meta_model.time_range),
                        rel_tol=OKAY_ACCURACY)
