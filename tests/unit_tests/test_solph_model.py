# -*- coding: utf-8 -*-
"""
Tests for the MTRESS solph model.
"""

import pytest

import datetime
import pandas as pd

from mtress import carriers, Connection, Location, MetaModel, SolphModel
from mtress.technologies.grid_connection import ElectricityGridConnection


def test_minimal_initialisation_with_date_range():
    first_index = "2021-07-10 00:00:00"
    last_index = "2021-07-10 15:15:00"
    frequency = "15T"
    date_range = pd.date_range(
        start=first_index,
        end=last_index,
        freq=frequency,
    )
    solph_model = SolphModel(meta_model=MetaModel(), timeindex=date_range)
    assert solph_model.energy_system.timeindex.freq == frequency
    assert (
        datetime.datetime.strptime(first_index, "%Y-%m-%d %H:%M:%S")
        == solph_model.energy_system.timeindex[0]
    )
    assert (
        datetime.datetime.strptime(last_index, "%Y-%m-%d %H:%M:%S")
        == solph_model.energy_system.timeindex[-1]
    )


def test_minimal_initialisation_with_time_index_dict():
    first_index = "2021-07-10 00:00:00"
    last_index = "2021-07-10 15:15:00"
    frequency = "15T"
    solph_model = SolphModel(
        meta_model=MetaModel(),
        timeindex={
            "start": first_index,
            "end": last_index,
            "freq": frequency,
        },
    )
    assert solph_model.energy_system.timeindex.freq == frequency
    assert (
        datetime.datetime.strptime(first_index, "%Y-%m-%d %H:%M:%S")
        == solph_model.energy_system.timeindex[0]
    )
    assert (
        datetime.datetime.strptime(last_index, "%Y-%m-%d %H:%M:%S")
        == solph_model.energy_system.timeindex[-1]
    )


def test_build_model_with_connected_electricity():
    house_1 = Location(name="house_1")
    house_1.add(carriers.ElectricityCarrier())
    gc1 = ElectricityGridConnection()
    house_1.add(gc1)

    house_2 = Location(name="house_2")
    house_2.add(carriers.ElectricityCarrier())
    gc2 = ElectricityGridConnection()
    house_2.add(gc2)

    meta_model = MetaModel(locations=[house_1, house_2])
    meta_model.add(Connection(house_1, house_2, ElectricityGridConnection))
    solph_model = SolphModel(
        meta_model=meta_model,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 15:15:00",
            "freq": "15T",
        },
    )
    solph_model.build_solph_model()

    assert gc2.grid_import in gc1.grid_export.outputs


def test_build_model_with_connected_electricity_missing_connection():
    house_1 = Location(name="house_1")
    house_2 = Location(name="house_2")

    meta_model = MetaModel(locations=[house_1, house_2])
    meta_model.add(Connection(house_1, house_2, ElectricityGridConnection))

    with pytest.raises(KeyError):
        SolphModel(
            meta_model=meta_model,
            timeindex={
                "start": "2021-07-10 00:00:00",
                "end": "2021-07-10 15:15:00",
                "freq": "15T",
            },
        )
