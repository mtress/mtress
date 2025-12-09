# -*- coding: utf-8 -*-
"""
Tests for the MTRESS heat carrier.
"""

import math

import pytest
import pandas as pd

from mtress import MetaModel
from mtress import SolphModel
from mtress.carriers import HeatCarrier


def test_heat_carrier_initialisation():
    with pytest.raises(TypeError):
        # temperatures need to be defined
        HeatCarrier()

    # temperature levels will be sorted internally
    temperatures = [10, 80, 35, -10, 75]
    heat_carrier = HeatCarrier(
        temperature_levels=temperatures,
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


def test_heat_carrier_build():
    solph_model = SolphModel(
        meta_model=MetaModel(),
        timeindex=pd.date_range("2025-01-01", periods=3, freq="h"),
    )

    temperature_levels = [10, 20]

    hc = HeatCarrier(
        temperature_levels=temperature_levels
    )  # two levels -> two nodes
    hc.register_solph_model(solph_model=solph_model)
    hc.build_core()
    solph_model.energy_system.add(hc.node)

    # model has one node for the HeatCarrier containing two subnodes
    assert len(solph_model.energy_system.node) == 3

    for temperature_level in temperature_levels:
        assert (
            solph_model.energy_system.node[
                (f"T_{temperature_level}", "HeatCarrier")
            ].custom_properties["temperature"]
            == temperature_level
        )
