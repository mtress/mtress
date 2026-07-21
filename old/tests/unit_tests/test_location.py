# -*- coding: utf-8 -*-
"""
Tests for the MTRESS class Location
"""

from mtress import Location, carriers, demands


def test_get_carrier():
    name = "house_1"
    house_1 = Location(label=name)

    carrier = house_1.get_carrier(carriers.ElectricityCarrier)

    assert carrier.label == ("ElectricityCarrier", "house_1")
    assert isinstance(carrier, carriers.ElectricityCarrier)


def test_get_nodes_manually_added():
    name = "house_1"
    house_1 = Location(label=name)

    carrier0 = carriers.ElectricityCarrier(label="carrier0")
    carrier1 = carriers.ElectricityCarrier(label="carrier1")
    demand1 = demands.Electricity(label="demand1", time_series=[0, 1, 2])
    demand2 = demands.Electricity(label="demand2", time_series=[1, 2, 3])

    house_1.add(carrier0)
    house_1.add(carrier1)
    house_1.add(demand1)
    house_1.add(demand2)

    # carriers are returned by get_nodes_by_type
    assert carrier0 in house_1.get_nodes_by_type(carriers.ElectricityCarrier)
    assert carrier1 in house_1.get_nodes_by_type(carriers.ElectricityCarrier)

    # first added carrier of the type is returned
    assert carrier0 == house_1.get_carrier(carriers.ElectricityCarrier)

    # demands are returned by get_nodes_by_type
    assert demand1 in house_1.get_nodes_by_type(demands.Electricity)
    assert demand2 in house_1.get_nodes_by_type(demands.Electricity)
