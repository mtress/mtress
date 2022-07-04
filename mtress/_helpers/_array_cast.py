# -*- coding: utf-8 -*-
"""
Generic model to be used to model residential energy supply systems

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""
import numbers
import numpy as np
import pandas as pd


def numeric_array(data, length):
    if isinstance(data, numbers.Number):
        data = np.full(length, fill_value=data)
    elif isinstance(data, list) and len(data) == length:
        data = np.array(data)
    elif isinstance(data, pd.Series) and len(data) == length:
        data = data.to_numpy()
    elif isinstance(data, np.ndarray):
        pass
    else:
        raise ValueError

    return data


def cast_to_base_types(data):
    """
    Recursively casts common types to (nested) Python base types such as
    lists, dicts, and strings
    """
    if type(data) is dict:
        for key in data:
            data[key] = cast_to_base_types(data[key])
    elif type(data) is pd.Series:
        data = data.tolist()
    elif type(data) is pd.DatetimeIndex:
        data = [timestamp.strftime("%Y-%m-%dT%H:%M:%S%z") for timestamp in data.tolist()]

    elif type(data) is list:
        for chunk in data:
            chunk = cast_to_base_types(chunk)

    return data
