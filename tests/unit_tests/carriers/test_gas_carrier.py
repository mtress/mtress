# -*- coding: utf-8 -*-
"""
Tests for the MTRESS gas carrier.
"""

import pytest

from oemof.network import Node
from mtress._constants import EnergyType
from mtress.carriers import GasCarrier
from mtress.physics import HYDROGEN, NATURAL_GAS


def test_basic_initialisation():
    parent_node = Node("parent")
    gc = GasCarrier(location=parent_node)
    assert gc.label == ("GasCarrier", "parent")
    assert gc.parent == parent_node

    assert len(gc.inbound_interfaces[EnergyType.GAS]) == 0
    assert len(gc.outbound_interfaces[EnergyType.GAS]) == 0


def test_gas_carrier_levels():
    hydrogen_pressures = [1, 3, 5, 7]
    pressures = {
        HYDROGEN: hydrogen_pressures,
        NATURAL_GAS: [1, 6, 10, 7],
    }

    gas_carier = GasCarrier()
    gas_carier._levels = pressures

    assert gas_carier.levels == pressures
    assert gas_carier.levels[HYDROGEN] == hydrogen_pressures

    assert gas_carier.get_surrounding_levels(HYDROGEN, 3) == (3, 3)
    assert gas_carier.get_surrounding_levels(HYDROGEN, 4) == (3, 5)
    with pytest.raises(TypeError):
        # gas needs to be specified
        gas_carier.get_surrounding_levels(4)
