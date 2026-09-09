# -*- coding: utf-8 -*-
"""
Tests for the MTRESS EnergyQuality
"""

import sys
import pytest

from mtress import EnergyQuality
from mtress._helpers._testing import assert_every_element_is_same

def test_basic_initialisation():
    constant_value = 12
    constant_quality = EnergyQuality(constant_value)
    assert constant_quality.value == constant_value
    assert constant_quality.maximum == constant_value
    assert constant_quality.minimum == constant_value
    assert constant_quality.fixed
    with pytest.raises(RuntimeError, match="Tried to change the value"):
        constant_quality.value = 13

    time_series = [13, 37]
    fixed_quality = EnergyQuality(time_series)
    assert_every_element_is_same(fixed_quality.value, time_series)
    assert_every_element_is_same(fixed_quality.maximum, time_series)
    assert_every_element_is_same(fixed_quality.minimum, time_series)
    assert fixed_quality.fixed
    with pytest.raises(RuntimeError, match="Tried to change the value"):
        fixed_quality.value = 13


def test_fixed_initialisation():
    """initialisation with explicitly fixed values"""
    constant_value = 12
    constant_quality = EnergyQuality(constant_value, fixed=True)
    assert constant_quality.value == constant_value
    assert constant_quality.maximum == constant_value
    assert constant_quality.minimum == constant_value
    assert constant_quality.fixed
    with pytest.raises(RuntimeError, match="Tried to change the value"):
        constant_quality.value = 13

    time_series = [13, 37]
    fixed_quality = EnergyQuality(time_series, fixed=True)
    assert_every_element_is_same(fixed_quality.value, time_series)
    assert_every_element_is_same(fixed_quality.maximum, time_series)
    assert_every_element_is_same(fixed_quality.minimum, time_series)
    assert fixed_quality.fixed
    with pytest.raises(RuntimeError, match="Tried to change the value"):
        fixed_quality.value = 13


def test_limit_initialisation():
    initial_value = 12
    final_value = 14
    maximum_series = [20, 15]
    minimum_series = [0, 5]

    quality_with_maximum = EnergyQuality(initial_value, maximum=maximum_series)
    assert quality_with_maximum.value == initial_value
    assert quality_with_maximum.minimum == -sys.float_info.max
    assert_every_element_is_same(quality_with_maximum.maximum, maximum_series)
    assert not quality_with_maximum.fixed

    quality_with_maximum.value = final_value
    assert quality_with_maximum.value == final_value
    assert quality_with_maximum.minimum == final_value
    assert quality_with_maximum.maximum == final_value

    quality_with_minimum = EnergyQuality(initial_value, minimum=minimum_series)
    assert quality_with_minimum.value == initial_value
    assert quality_with_minimum.maximum == sys.float_info.max
    assert_every_element_is_same(quality_with_minimum.minimum, minimum_series)
    assert not quality_with_minimum.fixed

    quality_with_minimum.value = final_value
    assert quality_with_minimum.value == final_value
    assert quality_with_minimum.minimum == final_value
    assert quality_with_minimum.maximum == final_value


def test_impossible_kwarg_combinations():
    with pytest.raises(ValueError, match="Argument 'fixed' cannot be true"):
        EnergyQuality(12, minimum=11, fixed=True)
    with pytest.raises(ValueError, match="Argument 'fixed' cannot be true"):
        EnergyQuality(12, maximum=13, fixed=True)


def test_euqality():
    assert EnergyQuality(12) == EnergyQuality(12)
    assert EnergyQuality(12, minimum=11) == EnergyQuality(42, minimum=11)
    assert EnergyQuality(12, maximum=42) == EnergyQuality(42, maximum=42)
    assert EnergyQuality(12, minimum=0, maximum=42) == EnergyQuality(
        42, minimum=0, maximum=42
    )
    assert EnergyQuality(12, minimum=11) != EnergyQuality(12, minimum=12)
    assert EnergyQuality(12, maximum=42) != EnergyQuality(12, maximum=12)
    assert EnergyQuality(12, minimum=11) != EnergyQuality(12, maximum=12)


def test_later_limit():
    initial_value = 12
    maximum_series = [20, 15]
    minimum_series = [0, 5]

    quality = EnergyQuality(initial_value, fixed=False)
    assert quality.value == initial_value
    assert quality.minimum == -sys.float_info.max
    assert quality.maximum == sys.float_info.max
    assert not quality.fixed

    quality.maximum = maximum_series
    assert quality.value == initial_value
    assert quality.minimum == -sys.float_info.max
    assert_every_element_is_same(quality.maximum, maximum_series)
    assert not quality.fixed

    quality.minimum = minimum_series
    assert quality.value == initial_value
    assert_every_element_is_same(quality.minimum, minimum_series)
    assert_every_element_is_same(quality.maximum, maximum_series)
    assert not quality.fixed
