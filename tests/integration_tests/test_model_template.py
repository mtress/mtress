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


def test_booster():
    DHW_DEMAND = 0.3

    p2h_params = {
        "gas_boiler": {"thermal_output": 1},
        "demand": {
            "dhw": 3* [DHW_DEMAND/3]}}
    meta_model = run_model_template(custom_params=p2h_params)

    assert math.isclose(meta_model.thermal_demand(), 0.3)
    assert math.isclose(meta_model.heat_boiler(), 0.2, rel_tol=1e-5)
    assert math.isclose(meta_model.heat_p2h(), 0.1, rel_tol=1e-5)
    assert math.isclose(meta_model.el_demand(), 0.1, rel_tol=1e-5)


def test_booster_heat_drop():
    DHW_DEMAND = 0.3
    p2h_params = {
        "gas_boiler": {"thermal_output": 1},
        "demand": {
            "dhw": 3* [DHW_DEMAND/3]},
        "temperatures": {"heat_drop_exchanger_dhw": 10}}  # +50% for booster
    meta_model = run_model_template(custom_params=p2h_params)

    assert math.isclose(meta_model.thermal_demand(), 0.3)
    assert math.isclose(meta_model.heat_boiler(), 0.15, rel_tol=1e-5)
    assert math.isclose(meta_model.heat_p2h(), 0.15, rel_tol=1e-5)
    assert math.isclose(meta_model.el_demand(), 0.15, rel_tol=1e-5)


if __name__ == "__main__":
    test_booster()
