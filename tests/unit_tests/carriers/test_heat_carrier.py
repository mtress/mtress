# -*- coding: utf-8 -*-
"""
Tests for the MTRESS heat carrier.
"""

import math

import pytest

from mtress.carriers import HeatCarrier


def test_heat_carrier_with_reference():
    with pytest.raises(TypeError):
        # temperatures need to be defined
        HeatCarrier()

    # temperature levels will be sorted internally
    temperatures = [10, 80, 35, -10, 75]
    ref_temperature = 15
    heat_carrier = HeatCarrier(
        temperature_levels=temperatures,
        reference_temperature=ref_temperature,
    )
    assert heat_carrier.levels == sorted(temperatures)

    assert heat_carrier.get_surrounding_levels(15) == (10, 35)

    # neither matches an existing level
    assert heat_carrier.get_levels_between(9, 36) == [10, 35]
    # maximum matching existing level
    assert heat_carrier.get_levels_between(9, 35) == [10, 35]
    # minimum matching existing level
    assert heat_carrier.get_levels_between(10, 36) == [10, 35]
    # both matching existing levels
    assert heat_carrier.get_levels_between(10, 35) == [10, 35]
    # all levels below a given value
    assert heat_carrier.get_levels_between(-math.inf, 35) == [-10, 10, 35]
    # all levels above a given value
    assert heat_carrier.get_levels_between(10, math.inf) == [10, 35, 75, 80]
    # one intermediate level
    assert heat_carrier.get_levels_between(9, 11) == [10]
    # no intermediate levels
    assert heat_carrier.get_levels_between(12, 13) == []
    # test first two levels
    assert heat_carrier.get_levels_between(-15, 15) == [-10, 10]
    # test last two levels
    assert heat_carrier.get_levels_between(70, 85) == [75, 80]
    # minimum and maximum match, coincide with a level
    assert heat_carrier.get_levels_between(10, 10) == [10]
    # minimum and maximum match, do not coincide with a level
    assert heat_carrier.get_levels_between(15, 15) == []

    # wrong order, not matching existing levels
    with pytest.raises(ValueError):
        heat_carrier.get_levels_between(36, 9)

    # wrong order, matching existing levels
    with pytest.raises(ValueError):
        heat_carrier.get_levels_between(35, 10)

    reference_level = heat_carrier.reference_level
    assert reference_level == 2  # [-10, 10, (*15*), ...]
    assert heat_carrier.levels[reference_level] > ref_temperature
    assert heat_carrier.levels[reference_level - 1] < ref_temperature

    assert heat_carrier.levels_below_reference == [-10, 10]
    assert heat_carrier.levels_above_reference == [35, 75, 80]


def test_heat_carrier_without_reference():
    # reference temperature (default: 0) is added to the levels
    temperatures = [-10, 15, 35, 80]
    heat_carrier = HeatCarrier(
        temperature_levels=temperatures,
    )
    assert heat_carrier.levels == sorted(temperatures)

    assert heat_carrier.get_surrounding_levels(0) == (-10, 15)
    assert heat_carrier.get_surrounding_levels(15) == (15, 15)

    assert heat_carrier.reference_level == 1  # [-10, *0*, ...]

    assert heat_carrier.levels_above_reference == [15, 35, 80]
    assert heat_carrier.levels_below_reference == [-10]


def test_heat_carrier_without_low_temperatures():
    temperatures = [35, 80]
    heat_carrier = HeatCarrier(
        temperature_levels=temperatures,
        reference_temperature=15,
    )
    assert heat_carrier.levels_above_reference == temperatures
    assert heat_carrier.levels_below_reference == []


def test_heat_carrier_without_high_temperatures():
    temperatures = [-10, 10]
    heat_carrier = HeatCarrier(
        temperature_levels=temperatures,
        reference_temperature=15,
    )
    assert heat_carrier.levels_above_reference == []
    assert heat_carrier.levels_below_reference == temperatures
