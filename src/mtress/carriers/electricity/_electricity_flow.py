# -*- coding: utf-8 -*-
"""Flows to specify heat

SPDX-FileCopyrightText: Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)

SPDX-License-Identifier: MIT
"""

from oemof.solph import Flow

from ..._helpers._visualization import EnergyType

class EnergyFlowElectricity(Flow):
    def __init__(self, **kwargs):
        if "custom_properties" not in kwargs:
            kwargs["custom_properties"] = {}
        kwargs["custom_properties"].update(
            {
                "unit": "W",
                "energy_type": EnergyType.ELECTRICITY,
            }
        )
        super().__init__(**kwargs)
