# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

import numpy as np
import pandas as pd

from oemof.solph import EnergySystem

from mtress import MetaModel
from mtress.technologies import Photovoltaics


def test_photovoltaics(periods=24):
    meta_model = MetaModel()

    pv_system_params = dict(
        nominal_power=1,
        latitude=0,
        longitude=0,
        surface_tilt=0,
        surface_azimuth=180,
    )
    simulation_data = dict()

    pv = Photovoltaics(
        location="LocationA",
        name="pv",
        pv_system_params=pv_system_params,
        simulation_data=simulation_data,
    )

    assert np.all(pv.specific_generation < 1)
    assert sum(pv.specific_generation)/periods < 0.5

    return pv


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    pv_tech = test_photovoltaics(periods=24*365)
    plt.plot(pv_tech.specific_generation)

    plt.show()
