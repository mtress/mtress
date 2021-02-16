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


def test_power2heat_nodrop():
    p2h_params = {
        "power_to_heat": {"thermal_output": 1},
        "demand": {
            "heating": [0.2, 0.2, 0.2],  # Sum: 0.6
            "dhw": [0.1, 0.1, 0.1]}}  # Sum: 0.3
    meta_model = run_model_template(custom_params=p2h_params)

    assert math.isclose(meta_model.thermal_demand(), 0.9)
    assert math.isclose(meta_model.heat_p2h(), 0.9)
    assert math.isclose(meta_model.el_demand(), 0.9)


def test_power2heat_heat_drop():
    p2h_params = {
        "power_to_heat": {"thermal_output": 1},
        "demand": {
            "heating": [0.2, 0.2, 0.2],  # Sum: 0.6
            "dhw": [0.1, 0.1, 0.1]},  # Sum: 0.3
        "temperatures": {"heat_drop_exchanger_dhw": 10}}  # +50% DHW demand
    meta_model = run_model_template(custom_params=p2h_params)

    assert math.isclose(meta_model.thermal_demand(), 0.9)
    assert math.isclose(meta_model.heat_p2h(), 1.05)
    assert math.isclose(meta_model.el_demand(), 0.9)


if __name__ == "__main__":
    test_empty_template()
