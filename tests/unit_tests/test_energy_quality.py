# -*- coding: utf-8 -*-
"""
Tests for the MTRESS EnergyQuality
"""

from mtress import EnergyQuality
from mtress._helpers._testing import assert_every_element_is_same

def test_initialisation():
    constant_value = 12
    constant_quality = EnergyQuality(12)
    assert constant_quality.value == constant_value
    assert constant_quality.maximum == constant_value
    assert constant_quality.minimum == constant_value

    time_series = [13, 37]
    constant_quality = EnergyQuality(time_series)
    assert_every_element_is_same(constant_quality.value, time_series)
    assert_every_element_is_same(constant_quality.maximum, time_series)
    assert_every_element_is_same(constant_quality.minimum, time_series)
