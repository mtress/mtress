# -*- coding: utf-8 -*-
"""Specifications of different types of energy

SPDX-FileCopyrightText: Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)

SPDX-License-Identifier: MIT
"""

from enum import IntEnum

from oemof.solph import Bus
from oemof.solph import Flow
from oemof.solph._plumbing import Apply
from oemof.solph._plumbing import sequence


class EnergyType(IntEnum):
    UNDEFINED = 0
    ELECTRICITY = 1
    HEAT = 2
    GAS = 3


class EnergyQuality:
    """energy quality"""
    minimum = Apply(sequence)
    maximum = Apply(sequence)

    def __init__(
        self,
        candidates=None,
        minimum=None,
        maximum=None,
        fixed=False,
    ):
        if candidates is None:
            candidates = []
        self.candidates = candidates
        self.minimum = minimum
        self.maximum = maximum
        self.final = fixed


class TemperatureBus(Bus):
    def __init__(
        self,
        temperature,
        label=None,
        *,
        inputs=None,
        outputs=None,
        specific_heat_capacity=1.161,
        parent_node=None,
        balanced=True,
        custom_properties=None,
    ):
        super().__init__(
            label,
            inputs=inputs,
            outputs=outputs,
            parent_node=parent_node,
            balanced=balanced,
            custom_properties=custom_properties,
        )
        self.specific_heat_capacity = specific_heat_capacity
        self.temperature = temperature


class MassFlowHeat(Flow):
    def __init__(
        self,
        nominal_capacity=None,
        variable_costs=0,
        minimum=None,
        maximum=None,
        fix=None,
        positive_gradient_limit=None,
        negative_gradient_limit=None,
        full_load_time_max=None,
        full_load_time_min=None,
        integer=False,
        nonconvex=None,
        custom_properties=None,
    ):
        if custom_properties is None:
            custom_properties = {}
        custom_properties.update(
            {
                "unit": "kg/h",
                "energy_type": EnergyType.HEAT,
            }
        )
        super().__init__(
            nominal_capacity=nominal_capacity,
            variable_costs=variable_costs,
            minimum=minimum,
            maximum=maximum,
            fix=fix,
            positive_gradient_limit=positive_gradient_limit,
            negative_gradient_limit=negative_gradient_limit,
            full_load_time_max=full_load_time_max,
            full_load_time_min=full_load_time_min,
            integer=integer,
            nonconvex=nonconvex,
            custom_properties=custom_properties,
        )


class EnergyFlowHeat(Flow):
    def __init__(
        self,
        nominal_capacity=None,
        variable_costs=0,
        minimum=None,
        maximum=None,
        fix=None,
        positive_gradient_limit=None,
        negative_gradient_limit=None,
        full_load_time_max=None,
        full_load_time_min=None,
        integer=False,
        nonconvex=None,
        custom_properties=None,
    ):
        if custom_properties is None:
            custom_properties = {}
        custom_properties.update(
            {
                "unit": "W",
                "energy_type": EnergyType.HEAT,
            }
        )
        super().__init__(
            nominal_capacity=nominal_capacity,
            variable_costs=variable_costs,
            minimum=minimum,
            maximum=maximum,
            fix=fix,
            positive_gradient_limit=positive_gradient_limit,
            negative_gradient_limit=negative_gradient_limit,
            full_load_time_max=full_load_time_max,
            full_load_time_min=full_load_time_min,
            integer=integer,
            nonconvex=nonconvex,
            custom_properties=custom_properties,
        )
