# -*- coding: utf-8 -*-
"""
Tests for the bare MTRESS meta model.
"""

import pytest

from typing import Iterable

from mtress import Location, MetaModel
from mtress.carriers import Electricity
from mtress.carriers import Heat


def test_minimal_initialisation():
    meta_model = MetaModel()

    assert isinstance(meta_model.locations, Iterable)
    locations = list(meta_model.locations)
    assert not locations  # list should be empty

    house_1 = Location(name="house_1")
    meta_model.add_location(house_1)

    assert house_1 in meta_model.locations


def test_list_initialisation():
    house_1 = Location(name="house_1")
    house_2 = Location(name="house_2")
    house_3 = Location(name="house_3")

    meta_model = MetaModel(locations=[house_1, house_2])

    assert isinstance(meta_model.locations, Iterable)
    locations = list(meta_model.locations)
    assert locations  # list not should be empty

    assert house_1 in meta_model.locations
    assert house_2 in meta_model.locations
    assert house_3 not in meta_model.locations


def test_adding_connections():
    house_1 = Location(name="house_1")
    house_2 = Location(name="house_2")
    house_3 = Location(name="house_3")

    meta_model = MetaModel(locations=[house_1, house_2])

    meta_model.add_connection(house_1, house_2, Electricity)

    # house_3 is not added to the meta_model (yet)
    with pytest.raises(ValueError):
        meta_model.add_connection(house_2, house_3, Heat)

    connections = list(meta_model.connections)
    assert len(connections) == 1
    assert MetaModel.ConnectionDescriptor(house_1, house_2, Electricity) in meta_model.connections

    meta_model.add_location(house_3)
    meta_model.add_connection(house_2, house_3, Heat)
    connections = list(meta_model.connections)
    assert len(connections) == 2
    assert MetaModel.ConnectionDescriptor(house_1, house_2, Electricity) in meta_model.connections
    assert MetaModel.ConnectionDescriptor(house_2, house_3, Heat) in meta_model.connections
