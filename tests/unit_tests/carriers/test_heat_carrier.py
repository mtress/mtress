# -*- coding: utf-8 -*-
"""
Tests for the MTRESS heat carrier.
"""

from mtress._helpers._testing import assert_every_element_is_same

from mtress.carriers import HeatCarrier
from mtress.carriers.heat import TemperatureBus


def test_basic_initialisation():
    hc = HeatCarrier(label="label")
    assert len(hc.inbound_interfaces) == 0
    assert len(hc.outbound_interfaces) == 0


def test_init_temperature_levels():
    temperatures = [-10, 10, [35, 36], 75, 80]
    hc = HeatCarrier(label="heat", temperature_levels=temperatures)

    assert_every_element_is_same(list(hc.temperatures), temperatures)

    assert len(hc.inbound_interfaces[TemperatureBus]) == len(temperatures)
    assert len(hc.outbound_interfaces[TemperatureBus]) == len(temperatures)
