# -*- coding: utf-8 -*-

"""
Helper functions.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""
from ._array_cast import numeric_array
from ._util import get_from_dict, read_input_data, update_in_dict
from ._results import get_flows

__all__ = [
    "numeric_array",
    "get_from_dict",
    "read_input_data",
    "update_in_dict",
    "get_flows",
]
