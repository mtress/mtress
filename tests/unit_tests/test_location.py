# -*- coding: utf-8 -*-
"""
Tests for the MTRESS class Location
"""

from typing import Iterable

from mtress import Location, carriers, demands


def test_basic_initialisation():
    name = "house_1"
    house_1 = Location(name=name)

    assert house_1.name == "house_1"
    assert isinstance(house_1.components, Iterable)


def test_add_carrier():
    name = "house_1"
    house_1 = Location(name=name)

    carrier1 = carriers.ElectricityCarrier()
    carrier2 = carriers.ElectricityCarrier()

    house_1.add(carrier1)
    assert house_1.get_carrier(carriers.ElectricityCarrier) == carrier1

    # carrier2 replaces carrier1
    house_1.add(carrier2)
    assert house_1.get_carrier(carriers.ElectricityCarrier) == carrier2


def test_add_component():
    name = "house_1"
    house_1 = Location(name=name)

    carrier0 = carriers.ElectricityCarrier()
    carrier1 = carriers.ElectricityCarrier()
    demand1 = demands.Electricity(name="demand1", time_series=[0, 1, 2])
    demand2 = demands.Electricity(name="demand2", time_series=[1, 2, 3])

    house_1.add(carrier0)
    house_1.add(carrier1)
    house_1.add(demand1)
    house_1.add(demand2)

    # carriers are not returned by get_technology
    assert carrier0 not in house_1.get_technology(carriers.ElectricityCarrier)
    assert carrier1 not in house_1.get_technology(carriers.ElectricityCarrier)

    # demands are returned by get_technology
    assert demand1 in house_1.get_technology(demands.Electricity)
    assert demand2 in house_1.get_technology(demands.Electricity)

    # carrier0 is overwitten by carrier1
    assert carrier0 not in house_1.components

    # all other components are in this Iterable
    assert carrier1 in house_1.components
    assert demand1 in house_1.components
    assert demand2 in house_1.components
