# -*- coding: utf-8 -*-
"""
Tests for the bare MTRESS meta model.
"""

import datetime
import pandas as pd

from mtress import MetaModel


def test_minimal_initialisation_with_date_range():
    first_index = "2021-07-10 00:00:00"
    last_index = "2021-07-10 15:15:00"
    frequency = "15T"
    date_range = pd.date_range(
        start=first_index,
        end=last_index,
        freq=frequency,
    )
    meta_model = MetaModel(time_index=date_range)
    assert meta_model.energy_system.timeindex.freq == frequency
    assert (
        datetime.datetime.strptime(first_index, "%Y-%m-%d %H:%M:%S")
        == meta_model.energy_system.timeindex[0]
    )
    assert (
        datetime.datetime.strptime(last_index, "%Y-%m-%d %H:%M:%S")
        == meta_model.energy_system.timeindex[-1]
    )


def test_minimal_initialisation_with_time_index_dict():
    first_index = "2021-07-10 00:00:00"
    last_index = "2021-07-10 15:15:00"
    frequency = "15T"
    meta_model = MetaModel(time_index={
        "start": first_index,
        "end": last_index,
        "freq": frequency,
    })
    assert meta_model.energy_system.timeindex.freq == frequency
    assert (
        datetime.datetime.strptime(first_index, "%Y-%m-%d %H:%M:%S")
        == meta_model.energy_system.timeindex[0]
    )
    assert (
        datetime.datetime.strptime(last_index, "%Y-%m-%d %H:%M:%S")
        == meta_model.energy_system.timeindex[-1]
    )
