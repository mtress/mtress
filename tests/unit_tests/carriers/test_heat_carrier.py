# -*- coding: utf-8 -*-
"""
Tests for the MTRESS heat carrier.
"""

import math

import pytest
from oemof.network import Node
from mtress._constants import EnergyType
from mtress.carriers import HeatCarrier


def test_basic_initialisation():
    parent_node = Node("parent")
    hc = HeatCarrier(parent_node=parent_node)
    assert hc.label == "HeatCarrier"
    assert hc.parent == parent_node

    assert len(hc._inbound_interfaces[EnergyType.HEAT]) == 0
    assert len(hc._outbound_interfaces[EnergyType.HEAT]) == 0


def test_temperatures():
    temperatures = [-10, 10, 35, 75, 80]
    heat_carrier = HeatCarrier()
    heat_carrier._levels = temperatures
    assert heat_carrier.levels == temperatures

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
