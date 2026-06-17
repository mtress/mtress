# -*- coding: utf-8 -*-
"""
Tests for the MTRESS heat carrier.
"""

import math

import pytest
from mtress._energy_types import EnergyType
from mtress.carriers import HeatCarrier


def test_basic_initialisation():
    hc = HeatCarrier(label="label")
    assert len(hc.inbound_interfaces[HeatCarrier]) == 0
    assert len(hc.outbound_interfaces[HeatCarrier]) == 0


def test_temperature_levels():
    temperatures = [-10, 10, 35, 75, 80]
    hc = HeatCarrier(label="heat", temperature_levels=temperatures)
    hc._levels = temperatures
    assert hc.levels == temperatures

    assert len(hc.inbound_interfaces[HeatCarrier]) == len(temperatures)
    assert len(hc.outbound_interfaces[HeatCarrier]) == len(temperatures)

    assert hc.get_surrounding_levels(15) == (10, 35)

    # neither matches an existing level
    assert hc.get_levels_between(9, 36) == [10, 35]
    # maximum matching existing level
    assert hc.get_levels_between(9, 35) == [10, 35]
    # minimum matching existing level
    assert hc.get_levels_between(10, 36) == [10, 35]
    # both matching existing levels
    assert hc.get_levels_between(10, 35) == [10, 35]
    # all levels below a given value
    assert hc.get_levels_between(-math.inf, 35) == [-10, 10, 35]
    # all levels above a given value
    assert hc.get_levels_between(10, math.inf) == [10, 35, 75, 80]
    # one intermediate level
    assert hc.get_levels_between(9, 11) == [10]
    # no intermediate levels
    assert hc.get_levels_between(12, 13) == []
    # test first two levels
    assert hc.get_levels_between(-15, 15) == [-10, 10]
    # test last two levels
    assert hc.get_levels_between(70, 85) == [75, 80]
    # minimum and maximum match, coincide with a level
    assert hc.get_levels_between(10, 10) == [10]
    # minimum and maximum match, do not coincide with a level
    assert hc.get_levels_between(15, 15) == []

    # wrong order, not matching existing levels
    with pytest.raises(ValueError):
        hc.get_levels_between(36, 9)

    # wrong order, matching existing levels
    with pytest.raises(ValueError):
        hc.get_levels_between(35, 10)
