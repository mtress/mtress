# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""
import json
import os
import math
import pandas as pd

from oemof.solph import views, processing

from meta_model.enaq_meta_model import ENaQMetaModel


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
    meta_model = ENaQMetaModel(**params)

    meta_model.model.solve(solver="cbc",
                           solve_kwargs={'tee': False},
                           solver_io='lp',
                           cmdline_options={'ratio': 0.01})

    meta_model.energy_system.results['main'] = views.convert_keys_to_strings(
        processing.results(meta_model.model))

    return meta_model


def test_empty_template():
    meta_model = run_model_template()

    assert meta_model.thermal_demand() == 0
    assert meta_model.el_demand() == 0
    assert meta_model.el_production() == 0


def test_heating():
    heat_demand = 0.3

    params = {
        "gas_boiler": {"thermal_output": 1},
        "demand": {
            "heating": 3 * [heat_demand / 3]}}
    meta_model = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand(), heat_demand)
    assert math.isclose(meta_model.heat_boiler(), heat_demand, rel_tol=1e-5)
    assert math.isclose(meta_model.heat_p2h(), 0, rel_tol=1e-5)
    assert math.isclose(meta_model.el_demand(), 0, rel_tol=1e-5)


def test_booster():
    dhw_demand = 0.3

    params = {
        "gas_boiler": {"thermal_output": 1},
        "demand": {
            "dhw": 3 * [dhw_demand / 3]}}
    meta_model = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand(), dhw_demand)
    assert math.isclose(meta_model.heat_boiler(), dhw_demand*2/3, rel_tol=1e-5)
    assert math.isclose(meta_model.heat_p2h(), dhw_demand/3, rel_tol=1e-5)
    assert math.isclose(meta_model.el_demand(), dhw_demand/3, rel_tol=1e-5)


def test_booster_heat_drop():
    dhw_demand = 0.3
    params = {
        "gas_boiler": {"thermal_output": 1},
        "demand": {
            "dhw": 3 * [dhw_demand / 3]},
        "temperatures": {"heat_drop_exchanger_dhw": 10}}  # +50% for booster
    meta_model = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand(), dhw_demand)
    assert math.isclose(meta_model.heat_boiler(), dhw_demand/2, rel_tol=1e-5)
    assert math.isclose(meta_model.heat_p2h(), dhw_demand/2, rel_tol=1e-5)
    assert math.isclose(meta_model.el_demand(), dhw_demand/2, rel_tol=1e-5)


def test_fully_solar():
    """
    Solar thermal is present provides enough heat.
    """
    heat_demand = 1
    st_generation = 1

    st_generation = {"ST_20": 3 * [st_generation / 3],
                     "ST_40": 3 * [st_generation / 3]}
    st_generation = pd.DataFrame(
        st_generation,
        index=pd.date_range('1/1/2000', periods=3, freq='H'))

    params = {
        "solar_thermal": {
            "st_area": 1,
            "generation": st_generation
        },
        "demand": {"heating": 3 * [heat_demand / 3]},
        "temperatures": {"heat_drop_heating": 20}}
    meta_model = run_model_template(custom_params=params)

    assert math.isclose(meta_model.heat_solar_thermal(),
                        heat_demand,
                        rel_tol=1e-5)


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
            "st_area": 1,
            "generation": st_generation
        },
        "heat_storage": {"volume": 2},
        "demand": {"heating": 3 * [heat_demand / 3]},
        "temperatures": {"heat_drop_heating": 20}}
    meta_model = run_model_template(custom_params=params)

    assert math.isclose(meta_model.heat_solar_thermal(),
                        heat_demand,
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
            "st_area": 1,
            "generation": st_generation
        },
        "demand": {
            "heating": 3 * [heat_demand / 3]
        },
        "temperatures": {
            "heat_drop_heating": 20,
            "intermediate": [30]}}
    meta_model = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand(),
                        heat_demand,
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_boiler(),
                        heat_demand/2,
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_solar_thermal(),
                        heat_demand/2,
                        rel_tol=1e-5)


def test_partly_solar_bad_timing():
    """
    Solar thermal is present would provide enough heat.
    However, only 1/6th of it can be used because of the temperature level
    right in the middle between forward and backward flow temperatures
    and it is present only in one of three time steps.
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
            "st_area": 1,
            "generation": st_generation
        },
        "demand": {
            "heating": 3 * [heat_demand / 3]
        },
        "temperatures": {
            "heat_drop_heating": 20,
            "intermediate": [30]}}
    meta_model = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand(),
                        heat_demand,
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_boiler(),
                        heat_demand*5/6,
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_solar_thermal(),
                        heat_demand/6,
                        rel_tol=1e-5)


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
            "st_area": 1,
            "generation": st_generation},
        "demand": {
            "heating": 3 * [heat_demand / 3]},
        "heat_storage": {
            "volume": 1e3},  # gigantic storage, so capacity plays no role
        "temperatures": {
            "heat_drop_heating": 20,
            "intermediate": [30]}}
    meta_model = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand(),
                        heat_demand,
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_boiler(),
                        heat_demand/2,
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_solar_thermal(),
                        heat_demand/2,
                        rel_tol=1e-5)


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
            "st_area": 1,
            "generation": st_generation
        },
        "demand": {
            "heating": 3 * [heat_demand / 3]
        },
        "temperatures": {
            "heat_drop_heating": 20,
            "intermediate": [30]}}
    meta_model = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand(), heat_demand, rel_tol=1e-5)
    assert math.isclose(meta_model.heat_boiler(), heat_demand, rel_tol=1e-5)
    assert math.isclose(meta_model.heat_solar_thermal(), 0, abs_tol=1e-8)


def test_missing_heat():
    heat_demand = 0.3

    params = {
        "demand": {
            "heating": 3 * [heat_demand / 3]}}
    meta_model = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand(), heat_demand)
    assert math.isclose(meta_model.missing_heat().sum(),
                        heat_demand,
                        rel_tol=1e-5)


def test_chp():
    heat_demand = 0.3

    params = {
        "chp": {"gas_input": 2,
                "thermal_output": 1,
                "electric_output": 1},
        "demand": {
            "heating": 3 * [heat_demand / 3]}}
    meta_model = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand(), heat_demand)
    assert math.isclose(meta_model.heat_chp(), heat_demand, rel_tol=1e-5)
    assert math.isclose(meta_model.el_export().sum(),
                        heat_demand,
                        rel_tol=1e-5)


def test_heat_pump():
    heat_demand = 1
    design_cop = 4.6 * 0.6

    params = {
        "heat_pump": {"electric_input": 1},
        "geothermal_heat_source": {"thermal_output": 1},
        "demand": {
            "heating": 3 * [heat_demand / 3]},
        "temperatures": {"heating": 35}}
    meta_model = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand(), heat_demand)
    assert math.isclose(meta_model.heat_heat_pump(),
                        heat_demand,
                        rel_tol=1e-5)
    design_cop_heat = meta_model.el_import().sum() * design_cop
    assert math.isclose(design_cop_heat,
                        heat_demand,
                        rel_tol=2.5e-2)  # 2.5 % are good enough


if __name__ == "__main__":
    test_partly_solar_bad_timing()
