# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

__version__ = "3.0.0dev0"

from . import physics
from . import technologies
from ._meta_model import MetaModel
from ._run_mtress import (
    prepare_mtress_config,
    run_mtress,
)

__all__ = [
    "physics",
    "technologies",
    "MetaModel",
    "prepare_mtress_config",
    "run_mtress",
]
