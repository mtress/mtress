# -*- coding: utf-8 -*-
"""
Bus to specify gas pressure
SPDX-FileCopyrightText: Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)
SPDX-License-Identifier: MIT
"""

from oemof.solph import Bus
from oemof.solph._plumbing import _FakeSequence

from mtress._energy_types import EnergyQuality
from mtress._data_handler import TimeseriesSpecifier

class GasBus(Bus):

    def __init__(
        self,
        pressure: EnergyQuality | TimeseriesSpecifier,
        label=None,
        *,
        inputs=None,
        outputs=None,
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
        if isinstance(pressure, EnergyQuality):
            self._pressure = pressure
        else:
            self._pressure = EnergyQuality(pressure)
        self.custom_properties["pressure"] = self.pressure

    @property
    def quality_status(self):
        return self._quality_status

    @quality_status.setter
    def quality_status(self, value):
        self.custom_properties["quality_status"] = value
        self._quality_status = value

    @property
    def pressure(self):
        return self._pressure.value

    @property
    def energy_quality(self):
        return self._pressure

    @pressure.setter
    def pressure(self, value):
        self._pressure.value = value
        self.custom_properties["pressure"] = self.pressure

    def align_timeindex(self):
        n_time_intervals = len(self._energy_system.timeincrement)
        if isinstance(self.energy_quality.value, _FakeSequence):
            self.energy_quality.value.size = n_time_intervals
        if isinstance(self.energy_quality.minimum, _FakeSequence):
            self.energy_quality.minimum.size = n_time_intervals
        if isinstance(self.energy_quality.maximum, _FakeSequence):
            self.energy_quality.maximum.size = n_time_intervals
