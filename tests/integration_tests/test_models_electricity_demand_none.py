
# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""
import math

from test_core import (run_model_template,
                       HIGH_ACCURACY)


def test_pv_export():
    params = {"pv": {
        "nominal_power": 2,
        "feed_in_subsidy": 75,
        "spec_generation": [0, 2, 1]
    }}
    meta_model, params = run_model_template(custom_params=params)

    pv_timeseries = meta_model.aggregate_flows(meta_model.pv_el_flows)
    el_export_timeseries = meta_model.aggregate_flows(meta_model.electricity_export_flows)

    for i in range(3):
        assert math.isclose(pv_timeseries[i],
                            params["pv"]["nominal_power"]
                            * params["pv"]["spec_generation"][i])
        assert math.isclose(el_export_timeseries[i],
                            params["pv"]["nominal_power"]
                            * params["pv"]["spec_generation"][i])

    assert math.isclose(meta_model.operational_costs(),
                        -params["pv"]["nominal_power"]
                        * sum(params["pv"]["spec_generation"])
                        * params["pv"]["feed_in_tariff"],
                        abs_tol=HIGH_ACCURACY)