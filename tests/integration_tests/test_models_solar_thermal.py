# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""
import math
import pandas as pd

from test_core import (run_model_template,
                       HIGH_ACCURACY)


def test_fully_solar():
    """
    Solar thermal is present provides enough heat.
    """
    heat_demand = 1
    st_generation = 1

    st_generation = {"ST_20": 3 * [st_generation / 3],
                     "ST_30": 0,
                     "ST_40": 3 * [st_generation / 3]}
    st_generation = pd.DataFrame(
        st_generation,
        index=pd.date_range('1/1/2000', periods=3, freq='H'))

    params = {
        "solar_thermal": {
            "area": 1,
            "spec_generation": st_generation
        },
        "demand": {
            "heating": {
                "values": 3 * [heat_demand/3],
                "flow_temperature": 40,
                "return_temperature": 20}
        }}
    meta_model, params = run_model_template(custom_params=params)

    st_generation = meta_model.aggregate_flows(
        meta_model.solar_thermal_th_flows).sum()

    assert math.isclose(st_generation, heat_demand,
                        rel_tol=HIGH_ACCURACY)


def test_fully_solar_with_useless_storage():
    """
    Solar thermal is present and can provide enough heat.
    The storage does not have to be used.
    """
    heat_demand = 1
    st_generation = 3

    st_generation = {"ST_20": 3 * [st_generation / 3],
                     "ST_40": 3 * [st_generation / 3]}
    st_generation = pd.DataFrame(
        st_generation,
        index=pd.date_range('1/1/2000', periods=3, freq='H'))

    params = {
        "solar_thermal": {
            "area": 1,
            "spec_generation": st_generation
        },
        "heat_storage": {"volume": 2},
        "demand": {
            "heating": {
                "values": 3 * [heat_demand/3],
                "flow_temperature": 40,
                "return_temperature": 20}
        }}
    meta_model, params = run_model_template(custom_params=params)

    st_generation = meta_model.aggregate_flows(
        meta_model.solar_thermal_th_flows).sum()

    assert math.isclose(st_generation, heat_demand,
                        rel_tol=1e-3)  # good enough


def test_partly_solar():
    """
    Solar thermal is present would provide enough heat.
    However, only half of it can be used because of the temperature level
    right in the middle between forward and backward flow temperatures.
    """
    heat_demand = 1
    st_generation = 1

    st_generation = {"ST_20": 3 * [1e-9],
                     "ST_30": 3 * [st_generation / 3],
                     "ST_40": 3 * [1e-9]}
    st_generation = pd.DataFrame(
        st_generation,
        index=pd.date_range('1/1/2000', periods=3, freq='H'))

    params = {
        "gas_boiler": {"thermal_output": 1},
        "solar_thermal": {
            "area": 1,
            "spec_generation": st_generation
        },
        "demand": {
            "heating": {
                "values": 3 * [heat_demand/3],
                "flow_temperature": 40,
                "return_temperature": 20}
        },
        "temperatures": {
            "additional": [30]}}
    meta_model, params = run_model_template(custom_params=params)

    thermal_demand = meta_model.aggregate_flows(meta_model.demand_th_flows).sum()
    boiler_generation = meta_model.aggregate_flows(meta_model.boiler_th_flows).sum()
    st_generation = meta_model.aggregate_flows(meta_model.solar_thermal_th_flows).sum()

    assert math.isclose(thermal_demand, heat_demand,
                        rel_tol=HIGH_ACCURACY)
    assert math.isclose(boiler_generation, heat_demand/2,
                        rel_tol=HIGH_ACCURACY)
    assert math.isclose(st_generation, heat_demand/2,
                        rel_tol=HIGH_ACCURACY)


def test_partly_solar_bad_timing():
    """
    Solar thermal is present would provide enough heat.
    However, only 1/6th of it can be used because of the temperature level
    right in the middle between forward and backward flow temperatures
    and it is present only in one of three time steps.
    """
    heat_demand = 1
    st_generation = 1

    st_generation = {"ST_20": 3 * [0],
                     "ST_30": [0, st_generation, 0],
                     "ST_40": 3 * [0]}
    st_generation = pd.DataFrame(
        st_generation,
        index=pd.date_range('1/1/2000', periods=3, freq='H'))

    params = {
        "gas_boiler": {"thermal_output": 1},
        "solar_thermal": {
            "area": 1,
            "spec_generation": st_generation
        },
        "demand": {
            "heating": {
                "values": 3 * [heat_demand/3],
                "flow_temperature": 40,
                "return_temperature": 20}
        },
        "temperatures": {
            "additional": [30]}}
    meta_model, params = run_model_template(custom_params=params)

    thermal_demand = meta_model.aggregate_flows(meta_model.demand_th_flows).sum()
    boiler_generation = meta_model.aggregate_flows(meta_model.boiler_th_flows).sum()
    st_generation = meta_model.aggregate_flows(meta_model.solar_thermal_th_flows).sum()

    assert math.isclose(thermal_demand, heat_demand,
                        rel_tol=HIGH_ACCURACY)
    assert math.isclose(boiler_generation, heat_demand*5/6,
                        rel_tol=HIGH_ACCURACY)
    assert math.isclose(st_generation, heat_demand/6,
                        rel_tol=HIGH_ACCURACY)


def test_partly_solar_with_storage():
    """
    Solar thermal is present would provide enough heat.
    However, only half of it can be used because of the temperature level
    right in the middle between forward and backward flow temperatures.
    The timing is compensated by a storage.
    """
    heat_demand = 1
    st_generation = 1

    st_generation = {"ST_20": 3 * [1e-9],
                     "ST_30": [1e-9, st_generation, 1e-9],
                     "ST_40": 3 * [1e-9]}
    st_generation = pd.DataFrame(
        st_generation,
        index=pd.date_range('1/1/2000', periods=3, freq='H'))

    params = {
        "gas_boiler": {"thermal_output": 1},
        "solar_thermal": {
            "area": 1,
            "spec_generation": st_generation},
        "demand": {
            "heating": {
                "values": 3 * [heat_demand/3],
                "flow_temperature": 40,
                "return_temperature": 20}
        },
        "heat_storage": {
            "volume": 1e3},  # gigantic storage, so capacity plays no role
        "temperatures": {
            "additional": [30]}}
    meta_model, params = run_model_template(custom_params=params)

    thermal_demand = meta_model.aggregate_flows(meta_model.demand_th_flows).sum()
    boiler_generation = meta_model.aggregate_flows(meta_model.boiler_th_flows).sum()
    st_generation = meta_model.aggregate_flows(meta_model.solar_thermal_th_flows).sum()

    assert math.isclose(thermal_demand, heat_demand,
                        rel_tol=HIGH_ACCURACY)
    assert math.isclose(boiler_generation, heat_demand/2,
                        rel_tol=HIGH_ACCURACY)
    assert math.isclose(st_generation, heat_demand/2,
                        rel_tol=HIGH_ACCURACY)


def test_useless_solar():
    """
    Solar thermal is present but useless,
    as it only provides heat at backward flow temperature.
    """
    heat_demand = 1
    st_generation = 1

    st_generation = {"ST_20": 3 * [st_generation / 3],
                     "ST_30": 3 * [1e-9],
                     "ST_40": 3 * [1e-9]}
    st_generation = pd.DataFrame(
        st_generation,
        index=pd.date_range('1/1/2000', periods=3, freq='H'))

    params = {
        "gas_boiler": {"thermal_output": 1},
        "solar_thermal": {
            "area": 1,
            "spec_generation": st_generation
        },
        "demand": {
            "heating": {
                "values": 3 * [heat_demand/3],
                "flow_temperature": 40,
                "return_temperature": 20}
        },
        "temperatures": {
            "additional": [30]}}
    meta_model, params = run_model_template(custom_params=params)

    thermal_demand = meta_model.aggregate_flows(meta_model.demand_th_flows).sum()
    boiler_generation = meta_model.aggregate_flows(meta_model.boiler_th_flows).sum()
    st_generation = meta_model.aggregate_flows(meta_model.solar_thermal_th_flows).sum()

    assert math.isclose(thermal_demand, heat_demand,
                        rel_tol=HIGH_ACCURACY)
    assert math.isclose(boiler_generation, heat_demand,
                        rel_tol=HIGH_ACCURACY)
    assert math.isclose(st_generation, 0,
                        abs_tol=1e-8)


if __name__ == "__main__":
    test_fully_solar()
