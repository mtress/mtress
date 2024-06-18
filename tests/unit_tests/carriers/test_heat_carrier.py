# -*- coding: utf-8 -*-
"""
Tests for the MTRESS heat carrier.
"""

import pytest

from mtress.carriers import HeatCarrier


def test_heat_carrier_with_reference():
    with pytest.raises(TypeError):
        # temperatures need to be defined
        HeatCarrier()

    # temperature levels will be sorted internally
    temperatures = [10, 15, 80, 35, -10]
    ref_temperature = 15
    heat_carier = HeatCarrier(
        temperature_levels=temperatures,
        reference_temperature=ref_temperature,
    )
    assert heat_carier.levels == sorted(temperatures)

    assert heat_carier.get_surrounding_levels(15) == (15, 15)
    assert heat_carier.get_surrounding_levels(20) == (15, 35)

    assert heat_carier.get_levels_between(10, 35) == [10, 15, 35]
    
    reference_level = heat_carier.reference_level
    assert reference_level == 2  # [-10, 10, *15*, ...]
    assert heat_carier.levels[reference_level] == ref_temperature

    assert heat_carier.levels_above_reference == [35, 80]
    assert heat_carier.levels_below_reference == [-10, 10]
    
def test_heat_carrier_without_reference():
    # reference temperature (default: 0) is added to the levels
    temperatures = [-10, 15, 35, 80]
    heat_carier = HeatCarrier(
        temperature_levels=temperatures,
    )
    assert heat_carier.levels == sorted(temperatures + [0])

    assert heat_carier.get_surrounding_levels(0) == (0, 0)
    assert heat_carier.get_surrounding_levels(-5) == (-10, 0)

    assert heat_carier.reference_level == 1  # [-10, *0*, ...]

    assert heat_carier.levels_above_reference == [15, 35, 80]
    assert heat_carier.levels_below_reference == [-10]


def test_heat_carrier_without_low_temperatures():
    temperatures = [35, 80]
    heat_carier = HeatCarrier(
        temperature_levels=temperatures,
        reference_temperature=15,
    )
    assert heat_carier.levels_above_reference == temperatures
    assert heat_carier.levels_below_reference == []


def test_heat_carrier_without_high_temperatures():
    temperatures = [-10, 10]
    heat_carier = HeatCarrier(
        temperature_levels=temperatures,
        reference_temperature=15,
    )
    assert heat_carier.levels_above_reference == []
    assert heat_carier.levels_below_reference == temperatures

