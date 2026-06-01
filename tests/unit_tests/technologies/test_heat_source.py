# -*- coding: utf-8 -*-

import numpy as np
import pytest

from oemof import solph

from mtress.technologies import HeatSource
from mtress import EnergyType


class TestHeatSource:

    label = "source"
    reservoir_temperature = np.array([0, 15, 55, -8.5])
    nominal_power = 10000
    conductivity_gain_factor = 200 / nominal_power

    def test_binary_source(self):
        src = HeatSource(
            label=self.label,
            reservoir_temperature=self.reservoir_temperature,
            nominal_power=self.nominal_power,
        )
        assert np.array_equal(
            src.reservoir_temperature,
            self.reservoir_temperature,
        )

        assert len(src.subnodes) == 6

        assert len(src.inbound_interfaces) == 1
        assert len(src.outbound_interfaces) == 1

        assert len(src.inbound_interfaces[EnergyType.HEAT]) == 1
        assert len(src.outbound_interfaces[EnergyType.HEAT]) == 1

        converters = [
            subnode for subnode in src.subnodes if isinstance(
                subnode, solph.components.Converter
            )
        ]
        assert len(converters) == 0 # only outlet is hother than reservoir
        [outlet] = src.outbound_interfaces[EnergyType.HEAT]
        assert outlet.custom_properties["temperature"] == 100

        # set outlet temperature to lower value and update converter
        outlet.custom_properties["temperature"] = 50
        src._update_source_converters()

        assert len(src.subnodes) == 7
        converters = [
            subnode for subnode in src.subnodes if isinstance(
                subnode, solph.components.Converter
            )
        ]
        [converter] = converters
        np.testing.assert_allclose(
            converter.conversion_factors[src._bus_utilisation],
            np.full(4, 0.5*116.1),
        )
        assert converter.inputs[src._bus_source].max == [0, 0, 1, 0]
        assert converter.conversion_factors[src._bus_source] == pytest.approx(
            0.5 * 116.1
        )
        np.testing.assert_allclose(
            converter.conversion_factors[src._bus_utilisation],
            np.full(4, 0.5 * 116.1),
        )

        outlet.custom_properties["temperature"] = 100
        src._update_source_converters()
        assert converter.inputs[src._bus_source].max == [0, 0, 0, 0]
        assert converter.conversion_factors[src._bus_source] == pytest.approx(
            116.1
        )

        b_t30 = solph.Bus(
            label="T_30",
            custom_properties={
                "temperature": 30,
            },
        )
        src.inbound_interfaces[EnergyType.HEAT].append(b_t30)

        assert len(src.subnodes) == 7  # no new subnodes, yet

        assert len(src.inbound_interfaces[EnergyType.HEAT]) == 2
        assert len(src.outbound_interfaces[EnergyType.HEAT]) == 1

        src._update_source_converters()
        assert len(src.subnodes) == 7  # created new converter

        src.outbound_interfaces[EnergyType.HEAT].append(b_t30)
        assert len(src.inbound_interfaces[EnergyType.HEAT]) == 2
        assert len(src.outbound_interfaces[EnergyType.HEAT]) == 2

        src._update_source_converters()
        # created new converter: (40 -> 30)
        assert len(src.subnodes) == 8

        b_t130 = solph.Bus(
            label="T_130",
            custom_properties={
                "temperature": 130,  # highter than maximum
            },
        )
        src.inbound_interfaces[EnergyType.HEAT].append(b_t130)
        src._update_source_converters()
        assert len(src.subnodes) == 8  # created no converters

        b_t60 = solph.Bus(
            label="T_60",
            custom_properties={
                "temperature": 60,  # highter than max(reservoir_temperauture)
            },
        )
        src.inbound_interfaces[EnergyType.HEAT].append(b_t60)
        src._update_source_converters()
        assert len(src.subnodes) == 8  # created no converters

    def test_conductive_source(self):
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

    def test_non_thermal_gain_source(self):
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
