# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""
import math
import numpy as np

from test_core import (run_model_template)


def test_demand_only():
    electricity_demand_local = [0.2, 0.1, 0.1]

    params = {
        "co2": {
            "el_in": 0.4,
            "el_out": -0.4
        },
        "demand": {
            "electricity": electricity_demand_local,
        },
    }
    meta_model, params = run_model_template(custom_params=params)

    assert math.isclose(
        meta_model.aggregate_flows(meta_model.electricity_import_flows).sum(),
        sum(electricity_demand_local),
        abs_tol=1e-5
    )

    assert math.isclose(
        meta_model.co2_emission(accuracy=5),
        sum(electricity_demand_local * params["co2"]["el_in"]),
        abs_tol=1e-5
    )


def test_adjacent_renewables():
    electricity_demand_adjacent = np.full(3, 0.1)
    electricity_demand_local = [0.2, 0.1, 0.1]
    pv_generation = [0.1, 0.05, 0.5]
    electricity_supply_adjacent = [0.4, 0.5, 0.1]

    params = {
        "co2": {
            "el_in": 0.4,
            "el_out": 0.4
        },
        "demand": {
            "electricity": electricity_demand_local,
            "electricity_adjacent": electricity_demand_adjacent
        },
        "energy_cost": {
          "electricity": {
            "market": 30  # €/MWh
          }
        },
        "adjacent_renewables": electricity_supply_adjacent,
        "pv": {
            "nominal_power": 1,
            "spec_generation": pv_generation,
            "feed_in_subsidy": 0.01,
        }
    }
    meta_model, params = run_model_template(custom_params=params)

    print(meta_model.co2_emission(accuracy=5))

    assert math.isclose(
        meta_model.aggregate_flows(meta_model.electricity_import_flows).sum(),
        sum(np.maximum(
            np.array(electricity_demand_local) - np.array(pv_generation),
            np.zeros(3))),
        abs_tol=1e-5
    )


if __name__ == '__main__':
    test_adjacent_renewables()
