# -*- coding: utf-8 -*-
"""Bus to specify electricity

SPDX-FileCopyrightText: Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)

SPDX-License-Identifier: MIT
"""

from oemof.solph import Bus


class ElectricityBus(Bus):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
