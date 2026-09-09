# -*- coding: utf-8 -*-
"""Bus to specify heat

SPDX-FileCopyrightText: Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)

SPDX-License-Identifier: MIT
"""

from oemof.solph import Bus
from oemof.solph._plumbing import _FakeSequence

from mtress._data_handler import TimeseriesSpecifier
from ..._energy_quality import EnergyQuality

class TemperatureBus(Bus):

    def __init__(
        self,
        temperature: EnergyQuality | TimeseriesSpecifier,
        *,
        label=None,
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
        if isinstance(temperature, EnergyQuality):
            self._temperature = temperature
        else:
            self._temperature = EnergyQuality(temperature)
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
