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


def numeric_array(data, length=None):
    if length is None:
        length = len(data)
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
