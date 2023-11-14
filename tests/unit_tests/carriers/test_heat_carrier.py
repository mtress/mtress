# -*- coding: utf-8 -*-
"""
Tests for the MTRESS gas carrier.
"""

import pytest

from mtress.carriers import Heat as HeatCarrier


def test_heat_carrier_levels():
    with pytest.raises(TypeError):
        # teperatures need to be defined
        HeatCarrier()

    temperatures = [15, 35, 80]

    heat_carier = HeatCarrier(temperature_levels=temperatures)
    assert heat_carier.levels == temperatures

    assert heat_carier.get_surrounding_levels(15) == (15, 15)
    assert heat_carier.get_surrounding_levels(20) == (15, 35)
