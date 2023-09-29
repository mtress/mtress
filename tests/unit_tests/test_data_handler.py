# -*- coding: utf-8 -*-
"""
Tests for the MTRESS data handler.
"""

import pandas as pd
import pytest

from mtress._data_handler import DataHandler


@pytest.fixture
def date_range():
    first_index = "2021-07-10 00:00:00"
    last_index = "2021-07-10 01:00:00"
    frequency = "15T"
    return pd.date_range(
        start=first_index,
        end=last_index,
        freq=frequency,
    )


@pytest.fixture
def data_handler(date_range):
    return DataHandler(date_range)


class TestDataHandler:
    def test_list(self, data_handler):
        data_list = [1, 2, 3, 4, 5]
        data = data_handler.get_timeseries(data_list)

        assert (data == data_list).all()

    def test_series(self, data_handler):
        data_list = [1, 2, 3, 4, 5]
        data_series = pd.Series(data=data_list)
        data = data_handler.get_timeseries(data_series)

        assert (data.values == data_list).all()

        with pytest.raises(ValueError):
            # Series is too long
            data_list = [1, 2, 3, 4, 5, 6]
            data_series = pd.Series(data=data_list)
            data = data_handler.get_timeseries(data_series)

    def test_series_with_timeindex(self, date_range, data_handler):
        data_list = [1, 2, 3, 4, 5]
        data_series = pd.Series(data=data_list, index=date_range)
        data = data_handler.get_timeseries(data_series)

        assert (data == data_series).all()

        longer_date_range = pd.date_range(
            start=date_range[0] - 2 * date_range.freq,
            end=date_range[-1] + 2 * date_range.freq,
            freq=date_range.freq,
        )

        longer_data_list = [8, 9] + data_list + [6, 7]
        data_series = pd.Series(data=longer_data_list, index=longer_date_range)
        data = data_handler.get_timeseries(data_series)
