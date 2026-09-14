# -*- coding: utf-8 -*-

"""
Tests for the LayeredHeatStorage

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

SPDX-License-Identifier: MIT
"""

from mtress.carriers import HeatCarrier
from mtress.carriers.heat import TemperatureBus
from mtress.components import LayeredHeatStorage


def test_basic_initialisation():
    temperatures = [30, 35, 40, 50]  # use integers to be able to compare

    lhs = LayeredHeatStorage(
        "lhs",
        diameter=0.5,
        volume=1,
        temperature_levels=temperatures,
    )
    inbound = lhs.inbound_interfaces[TemperatureBus]
    outbound = lhs.outbound_interfaces[TemperatureBus]
    interface_temperatures = {
        int(t.temperature) for t in lhs.inbound_interfaces[TemperatureBus]
    }

    assert inbound == outbound
    assert len(inbound) == len(temperatures)

    assert set(temperatures) == interface_temperatures

    assert len(lhs.subnodes) == 2 * len(temperatures)
    for subnode in lhs.subnodes:
        assert subnode.custom_properties["temperature"] in temperatures
        assert len(subnode.inputs) == 1  # no losses -> independent layers
        assert len(subnode.outputs) == 1  # no losses -> independent layers


def test_connection_lossless():
    temperatures = [30, 35, 40, 50]

    lhs = LayeredHeatStorage(
        "lhs",
        diameter=0.5,
        volume=1,
        temperature_levels=temperatures,
    )
    hc = HeatCarrier("hc", temperature_levels=temperatures + [10])
    lhs._connect_to_carrier(hc)

    assert len(lhs.subnodes) == 2 * len(temperatures)
    for subnode in lhs.subnodes:
        assert subnode.custom_properties["temperature"] in temperatures
        if isinstance(subnode, TemperatureBus):
            assert len(subnode.inputs) == 2
            assert len(subnode.outputs) == 2
        else:
            assert len(subnode.inputs) == 1
            assert len(subnode.outputs) == 1
