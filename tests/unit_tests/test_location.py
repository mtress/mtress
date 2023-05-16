# -*- coding: utf-8 -*-
"""
Tests for the MTRESS class Location
"""

from typing import Iterable

from mtress import Location

def test_basic_initialisation():
    name = "house_1"
    house_1 = Location(name=name)

    assert house_1.name == "house_1"
    assert isinstance(house_1.components, Iterable)
