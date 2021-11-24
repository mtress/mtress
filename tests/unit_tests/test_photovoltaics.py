# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

import numpy as np
import pandas as pd

from oemof.solph import EnergySystem
from oemof.solph import Bus

from mtress.technologies import Photovoltaics


def test_photovoltaics(periods=24):
    time_index = pd.date_range('1/1/2000', periods=periods, freq='H')
    energy_system = EnergySystem(timeindex=time_index)

    pv_system_params = dict(
        nominal_power=1,
        latitude=0,
        longitude=0,
        surface_tilt=0,
        surface_azimuth=180,
    )
    simulation_data = dict()

    bus = Bus(label="bus")

    pv = Photovoltaics(
        pv_system_params,
        simulation_data,
        funding=0.1,
        out_bus_internal=bus,
        out_bus_external=bus,
        label="pv",
        energy_system=energy_system)

    assert np.all(pv.specific_generation < 1)
    assert sum(pv.specific_generation)/periods < 0.5

    return pv


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    pv_tech = test_photovoltaics(periods=24*365)
    plt.plot(pv_tech.specific_generation)

    plt.show()
