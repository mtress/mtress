# -*- coding: utf-8 -*-
"""Specifications of different types of energy

SPDX-FileCopyrightText: Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)

SPDX-License-Identifier: MIT
"""

from enum import IntEnum

from oemof.solph import Bus
from oemof.solph import Flow
from oemof.solph._plumbing import _FakeSequence
from oemof.solph._plumbing import Apply
from oemof.solph._plumbing import sequence


class EnergyType(IntEnum):
    UNDEFINED = 0
    ELECTRICITY = 1
    HEAT = 2
    GAS = 3


class EnergyQuality:
    """energy quality"""
    _value = Apply(sequence)
    _minimum = Apply(sequence)
    _maximum = Apply(sequence)

    def __init__(
        self,
        value,
        minimum=None,
        maximum=None,
        fixed=False,
    ):
        self._value = value
        self.minimum = minimum
        self.maximum = maximum
        self.fixed = fixed

    @property
    def minimum(self):
        if self.fixed:
            return self._value
        else:
            return self._minimum

    @minimum.setter
    def minimum(self, value):
        # TODO: forbid overwriting final values
        self._minimum = value

    @property
    def maximum(self):
        if self.fixed:
            return self._value
        else:
            return self._maximum

    @maximum.setter
    def maximum(self, value):
        # TODO: forbid overwriting final values
        self._maximum = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not self.fixed:
            self.fixed = True
            self._value = value
        else:
            raise RuntimeError(
                "Tried to change the value of an 'EnergyQuality' that has a"
                + " fixed value. (Setting a value after initialisation fixes"
                + " that value)."
            )


class QualityStatus(IntEnum):
    """Status of an energy quality, """
    UNDEFINED = 0
    PRELIMINARY_MIN = 1
    PRELIMINARY_MAX = 2
    INFERRED = 3
    FIXED = 4


class TemperatureBus(Bus):
    def __init__(
        self,
        temperature,
        quality_status=QualityStatus.FIXED,
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
        self.quality_status = quality_status
        self.specific_heat_capacity = specific_heat_capacity
        if isinstance(temperature, EnergyQuality):
            self._temperature = temperature
        else:
            self._temperature = EnergyQuality(
                temperature,
                fixed=(quality_status == QualityStatus.FIXED),
            )
        self.custom_properties["temperature"] = self.temperature

    @property
    def quality_status(self):
        return self._quality_status

    @quality_status.setter
    def quality_status(self, value):
        self.custom_properties["quality_status"] = value
        self._quality_status = value

    @property
    def specific_heat_capacity(self):
        return self._specific_heat_capacity

    @specific_heat_capacity.setter
    def specific_heat_capacity(self, value):
        self.custom_properties["specific_heat_capacity"] = value
        self._specific_heat_capacity = value

    @property
    def temperature(self):
        return self._temperature.value

    @property
    def energy_quality(self):
        return self._temperature

    @temperature.setter
    def temperature(self, value):
        self._temperature.value = value
        self.custom_properties["temperature"] = self.temperature

    def align_timeindex(self):
        n_time_intervals = len(self._energy_system.timeincrement)
        if isinstance(self.energy_quality.value, _FakeSequence):
            self.energy_quality.value.size = n_time_intervals
        if isinstance(self.energy_quality.minimum, _FakeSequence):
            self.energy_quality.minimum.size = n_time_intervals
        if isinstance(self.energy_quality.maximum, _FakeSequence):
            self.energy_quality.maximum.size = n_time_intervals


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
