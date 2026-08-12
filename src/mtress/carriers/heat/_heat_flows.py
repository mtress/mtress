# -*- coding: utf-8 -*-
"""Flows to specify heat

SPDX-FileCopyrightText: Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)

SPDX-License-Identifier: MIT
"""

from oemof.solph import Flow

from mtress._energy_types import EnergyType

class MassFlowHeat(Flow):
    def __init__(self, **kwargs):
        if "custom_properties" not in kwargs:
            kwargs["custom_properties"] = {}
        kwargs["custom_properties"].update(
            {
                "unit": "kg/h",
                "energy_type": EnergyType.HEAT,
            }
        )
        super().__init__(**kwargs)


class EnergyFlowHeat(Flow):
    def __init__(self, **kwargs):
        if "custom_properties" not in kwargs:
            kwargs["custom_properties"] = {}
        kwargs["custom_properties"].update(
            {
                "unit": "W",
                "energy_type": EnergyType.HEAT,
            }
        )
        super().__init__(**kwargs)
