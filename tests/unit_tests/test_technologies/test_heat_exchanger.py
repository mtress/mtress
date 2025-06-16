# -*- coding: utf-8 -*-

import numpy as np
import pytest

from mtress.technologies import HeatExchanger
from mtress.technologies import HeatSink
from mtress.technologies import HeatSource


def test_heat_source_initialisation():
    """Tests for initilisation (including gains helper)"""
    name = "source"
    reservoir_temperature = np.array([0, 15, 55, -8.5])
    nominal_power = 10000

    #with pytest.raises(TypeError, match="nominal_power"):
    #    _ = HeatSource(
    #        name=name,
    #        reservoir_temperature=reservoir_temperature,
    #    )

    with pytest.raises(ValueError, match="minimum_delta has to be > 1 °C"):
        _ = HeatSource(
            name=name,
            reservoir_temperature=reservoir_temperature,
            nominal_power=1,
            minimum_delta=0.5,
        )

    with pytest.raises(ValueError, match="minimum_delta has to be > 1 °C"):
        _ = HeatSource(
            name=name,
            reservoir_temperature=reservoir_temperature,
            nominal_power=1,
            minimum_delta=-4,
        )

    # basic initialisation
    src = HeatSource(
        name=name,
        reservoir_temperature=reservoir_temperature,
        nominal_power=nominal_power,
    )
    assert src.name is "source"
    assert np.array_equal(src.reservoir_temperature, reservoir_temperature)
    assert np.array_equal(src._normalised_gains(40), [0, 0, 1, 0])
    assert np.array_equal(src._normalised_gains(-5), [1, 1, 1, 0])

    # initialisation with conductive gains
    conductivity_gain_factor = 200 / nominal_power

    src = HeatSource(
        name=name,
        reservoir_temperature=reservoir_temperature,
        nominal_power=nominal_power,
        conductivity_gain_factor=conductivity_gain_factor,
    )
    assert np.allclose(src._normalised_gains(40), [0, 0, 0.3, 0])
    assert np.allclose(src._normalised_gains(-5), [0.1, 0.4, 1, 0])

    # initialisation with conductive and non-thermal gains
    non_thermal_gains = np.array([0, 1, 0.8, 0.4])

    src = HeatSource(
        name=name,
        reservoir_temperature=reservoir_temperature,
        nominal_power=nominal_power,
        conductivity_gain_factor=conductivity_gain_factor,
        non_thermal_gains=non_thermal_gains,
    )
    assert np.allclose(src._normalised_gains(40), [0, 0.5, 1, 0])
    assert np.allclose(src._normalised_gains(-5), [0.1, 1, 1, 0.33])
