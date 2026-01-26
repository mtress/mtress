# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

from ._location import Location
from ._meta_model import Connection, MetaModel
from ._solph_model import SolphModel


__version__ = "26.1.26"

__all__ = [
    "Connection",
    "Location",
    "MetaModel",
    "SolphModel",
]
