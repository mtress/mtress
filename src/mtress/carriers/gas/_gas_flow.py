# -*- coding: utf-8 -*-
"""
Flows to specify pressure

SPDX-FileCopyrightText: Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)

SPDX-License-Identifier: MIT
"""

from oemof.solph import Flow

from mtress._helpers._visualization import EnergyType


class MassFlowGas(Flow):
    def __init__(self, **kwargs):
        if "custom_properties" not in kwargs:
            kwargs["custom_properties"] = {}
        kwargs["custom_properties"].update(
            {
                "unit": "kg/h",
                "energy_type": EnergyType.GAS,
            }
        )
        super().__init__(**kwargs)
