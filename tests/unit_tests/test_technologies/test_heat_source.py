# -*- coding: utf-8 -*-

import numpy as np
import pytest

from mtress.technologies import HeatSource
from mtress import EnergyType


class TestHeatSource:

    label = "source"
    reservoir_temperature = np.array([0, 15, 55, -8.5])
    nominal_power = 10000
    conductivity_gain_factor = 200 / nominal_power

    def test_minimal_initialisation(self):
        src = HeatSource(
            label=self.label,
            reservoir_temperature=self.reservoir_temperature,
            nominal_power=self.nominal_power,
        )
        assert np.array_equal(
            src.reservoir_temperature,
            self.reservoir_temperature,
        )
        assert np.array_equal(src._normalised_gains(40), [0, 0, 1, 0])
        assert np.array_equal(src._normalised_gains(-5), [1, 1, 1, 0])

        assert len(src.inbound_interfaces) == 1
        assert len(src.outbound_interfaces) == 1

        assert len(src.inbound_interfaces[EnergyType.HEAT]) == 1
        assert len(src.outbound_interfaces[EnergyType.HEAT]) == 1

    def test_conductivity_initialisation(self):
        src = HeatSource(
            label=self.label,
            reservoir_temperature=self.reservoir_temperature,
            nominal_power=self.nominal_power,
            conductivity_gain_factor=self.conductivity_gain_factor,
        )
        assert np.allclose(src._normalised_gains(40), [0, 0, 0.3, 0])
        assert np.allclose(src._normalised_gains(-5), [0.1, 0.4, 1, 0])

        assert len(src.inbound_interfaces) == 1
        assert len(src.outbound_interfaces) == 1

        assert len(src.inbound_interfaces[EnergyType.HEAT]) == 1
        assert len(src.outbound_interfaces[EnergyType.HEAT]) == 1

    def test_non_thermal_initialisation(self):
        non_thermal_gains = np.array([0, 1, 0.8, 0.4])

        src = HeatSource(
            label=self.label,
            reservoir_temperature=self.reservoir_temperature,
            nominal_power=self.nominal_power,
            conductivity_gain_factor=self.conductivity_gain_factor,
            non_thermal_gains=non_thermal_gains,
        )
        assert np.allclose(src._normalised_gains(40), [0, 0.5, 1, 0])
        assert np.allclose(src._normalised_gains(-5), [0.1, 1, 1, 0.33])

        assert len(src.inbound_interfaces) == 1
        assert len(src.outbound_interfaces) == 1

        assert len(src.inbound_interfaces[EnergyType.HEAT]) == 1
        assert len(src.outbound_interfaces[EnergyType.HEAT]) == 1

    def test_minimum_delta_limit_check(self):
        with pytest.raises(ValueError, match="minimum_delta has to be > 1 °C"):
            _ = HeatSource(
                label="source",
                reservoir_temperature=42,
                nominal_power=1,
                minimum_delta=0.5,
            )

        with pytest.raises(ValueError, match="minimum_delta has to be > 1 °C"):
            _ = HeatSource(
                label="source",
                reservoir_temperature=42,
                nominal_power=1,
                minimum_delta=-4,
            )
