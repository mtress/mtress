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

from mtress.meta_model import MetaModel

HIGH_ACCURACY = 1e-5
OKAY_ACCURACY = 2.5e-2  # sometimes, 2.5 % are good enough


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
    return sum(gas_demand * np.array(params["energy_cost"]["fossil_gas"]))


def chp_revenue(export, own_consumption, params):
    # TODO: Consider funding hours per year
    feed_in_revenue = (export * (params["energy_cost"]["electricity"]["market"]
                       + params["chp"]["feed_in_subsidy"])).sum()
    oc_costs = own_consumption * (params["energy_cost"]['eeg_levy']
                                  - params["chp"]["own_consumption_subsidy"])
    return feed_in_revenue - oc_costs


def test_empty_template():
    meta_model, params = run_model_template()

    assert math.isclose(meta_model.thermal_demand().sum(), 0, abs_tol=1e-5)
    assert math.isclose(meta_model.el_demand().sum(), 0, abs_tol=1e-5)
    assert math.isclose(meta_model.el_production().sum(), 0, abs_tol=1e-5)
    assert math.isclose(meta_model.operational_costs(), 0, abs_tol=1e-5)


def test_gas_boiler():
    heat_demand = np.full(3, 0.1)

    params = {
        "gas_boiler": {"thermal_output": 1},
        "demand": {"heating": heat_demand}}
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand().sum(), heat_demand.sum())
    assert math.isclose(meta_model.heat_boiler().sum(),
                        heat_demand.sum(),
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_p2h().sum(), 0, rel_tol=1e-5)
    assert math.isclose(meta_model.el_demand().sum(), 0, rel_tol=1e-5)

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

    assert math.isclose(meta_model.thermal_demand().sum(), dhw_demand.sum())
    assert math.isclose(meta_model.heat_boiler().sum(),
                        gas_demand.sum(),
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_p2h().sum(), electricity_demand.sum(),
                        rel_tol=1e-5)
    assert math.isclose(meta_model.el_demand().sum(), electricity_demand.sum(),
                        rel_tol=1e-5)

    assert math.isclose(meta_model.operational_costs(),
                        electricity_costs(electricity_demand,
                                          params,
                                          meta_model.time_range)
                        + gas_costs(gas_demand, params),
                        rel_tol=1e-5)


def test_booster_heat_drop():
    dhw_demand = np.full(3, 0.1)
    electricity_demand = 0.5 * dhw_demand
    gas_demand = 0.5 * dhw_demand

    params = {
        "gas_boiler": {"thermal_output": 1},
        "demand": {"dhw": dhw_demand},
        "temperatures": {"heat_drop_exchanger_dhw": 10}}  # +50% for booster
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand().sum(), dhw_demand.sum())
    assert math.isclose(meta_model.heat_boiler().sum(),
                        gas_demand.sum(),
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_p2h().sum(),
                        electricity_demand.sum(),
                        rel_tol=1e-5)
    assert math.isclose(meta_model.el_demand().sum(),
                        electricity_demand.sum(),
                        rel_tol=1e-5)

    assert math.isclose(meta_model.operational_costs(),
                        electricity_costs(electricity_demand,
                                          params,
                                          meta_model.time_range)
                        + gas_costs(gas_demand, params),
                        rel_tol=1e-5)


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
            "area": 1,
            "spec_generation": st_generation
        },
        "demand": {"heating": 3 * [heat_demand / 3]},
        "temperatures": {"heat_drop_heating": 20}}
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(meta_model.heat_solar_thermal().sum(),
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
            "area": 1,
            "spec_generation": st_generation
        },
        "heat_storage": {"volume": 2},
        "demand": {"heating": 3 * [heat_demand / 3]},
        "temperatures": {"heat_drop_heating": 20}}
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(meta_model.heat_solar_thermal().sum(),
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
            "area": 1,
            "spec_generation": st_generation
        },
        "demand": {
            "heating": 3 * [heat_demand / 3]
        },
        "temperatures": {
            "heat_drop_heating": 20,
            "intermediate": [30]}}
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand().sum(),
                        heat_demand,
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_boiler().sum(),
                        heat_demand/2,
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_solar_thermal().sum(),
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
            "area": 1,
            "spec_generation": st_generation
        },
        "demand": {
            "heating": 3 * [heat_demand / 3]
        },
        "temperatures": {
            "heat_drop_heating": 20,
            "intermediate": [30]}}
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand().sum(),
                        heat_demand,
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_boiler().sum(),
                        heat_demand*5/6,
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_solar_thermal().sum(),
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
            "area": 1,
            "spec_generation": st_generation},
        "demand": {
            "heating": 3 * [heat_demand / 3]},
        "heat_storage": {
            "volume": 1e3},  # gigantic storage, so capacity plays no role
        "temperatures": {
            "heat_drop_heating": 20,
            "intermediate": [30]}}
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand().sum(),
                        heat_demand,
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_boiler().sum(),
                        heat_demand/2,
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_solar_thermal().sum(),
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
            "area": 1,
            "spec_generation": st_generation
        },
        "demand": {
            "heating": 3 * [heat_demand / 3]
        },
        "temperatures": {
            "heat_drop_heating": 20,
            "intermediate": [30]}}
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand().sum(),
                        heat_demand,
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_boiler().sum(),
                        heat_demand,
                        rel_tol=1e-5)
    assert math.isclose(meta_model.heat_solar_thermal().sum(),
                        0,
                        abs_tol=1e-8)


def test_missing_heat():
    heat_demand = 0.3

    params = {
        "demand": {
            "heating": 3 * [heat_demand / 3]}}
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand().sum(), heat_demand)
    assert math.isclose(meta_model.missing_heat().sum(),
                        heat_demand,
                        rel_tol=1e-5)


def test_heat_pump():
    heat_demand = np.full(3, 0.1)
    design_cop = 5
    electricity_demand = heat_demand/design_cop

    params = {
        "heat_pump": {"electric_input": 1,
                      "cop_0_35": design_cop},
        "geothermal_heat_source": {"thermal_output": 1},
        "demand": {
            "heating": heat_demand},
        "temperatures": {"heating": 35}}
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(meta_model.thermal_demand().sum(), heat_demand.sum())
    assert math.isclose(meta_model.heat_heat_pump().sum(),
                        heat_demand.sum(),
                        rel_tol=HIGH_ACCURACY)
    design_cop_heat = meta_model.el_import().sum() * design_cop
    assert math.isclose(design_cop_heat,
                        heat_demand.sum(),
                        rel_tol=OKAY_ACCURACY)
    assert math.isclose(meta_model.operational_costs(),
                        electricity_costs(electricity_demand,
                                          params,
                                          meta_model.time_range),
                        rel_tol=OKAY_ACCURACY)


def test_pv_export():
    params = {"pv": {
        "nominal_power": 2,
        "feed_in_tariff": 75,
        "spec_generation": [0, 2, 1]
    }}
    meta_model, params = run_model_template(custom_params=params)

    for i in range(3):
        assert math.isclose(meta_model.el_pv()[i],
                            params["pv"]["nominal_power"]
                            * params["pv"]["spec_generation"][i])
        assert math.isclose(meta_model.el_export()[i],
                            params["pv"]["nominal_power"]
                            * params["pv"]["spec_generation"][i])

    assert math.isclose(meta_model.operational_costs(),
                        -params["pv"]["nominal_power"]
                        * sum(params["pv"]["spec_generation"])
                        * params["pv"]["feed_in_tariff"],
                        abs_tol=HIGH_ACCURACY)


if __name__ == '__main__':
    test_heat_pump()
