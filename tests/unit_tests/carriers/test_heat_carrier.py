# -*- coding: utf-8 -*-
"""
Tests for the MTRESS heat carrier.
"""

import sys

import numpy as np

from mtress._helpers._testing import assert_every_element_is_same

from mtress.carriers import HeatCarrier
from mtress.carriers.heat import TemperatureBus
from mtress._energy_quality import EnergyQuality
from mtress._plumbing import sequence_compare


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


def test_level_autocreation():
    hc = HeatCarrier(label="heat")
    assert len(hc.inbound_interfaces) == 0
    assert len(hc.outbound_interfaces) == 0

    level10_1 = hc.get_level(10)
    assert len(hc.inbound_interfaces) == 1
    assert len(hc.outbound_interfaces) == 1

    level10_2 = hc.get_level(10)
    assert len(hc.inbound_interfaces) == 1
    assert len(hc.outbound_interfaces) == 1
    assert level10_2 == level10_1


def test_heat_carrier_overlap():
    [overlap_equal] = HeatCarrier._overlap(
        TemperatureBus(35),
        TemperatureBus(35),
    )
    assert overlap_equal == 35

    [overlap_diverge] = HeatCarrier._overlap(
        TemperatureBus([30, 25, 35]),
        TemperatureBus([30, 25, 25]),
    )
    assert sequence_compare(overlap_diverge, [30, 25, np.nan])

    overlap_cross = HeatCarrier._overlap(
        TemperatureBus([35, 36]),
        TemperatureBus([30, 35]),
    )
    assert len(overlap_cross) == 0

    [constant_in_range] = HeatCarrier._overlap(
        TemperatureBus(EnergyQuality(value=30, minimum=30 ,maximum=40)),
        TemperatureBus(35),
    )
    assert constant_in_range == 35

    [value_leaves_range] = HeatCarrier._overlap(
        TemperatureBus(EnergyQuality(value=30, minimum=30 ,maximum=40)),
        TemperatureBus([35, 40, 45]),
    )
    assert sequence_compare(value_leaves_range, [35, 40, np.nan])

    overlap_second_in_first_range = HeatCarrier._overlap(
        TemperatureBus(EnergyQuality(value=32, minimum=25 ,maximum=40)),
        TemperatureBus(EnergyQuality(value=30, minimum=30 ,maximum=35)),
    )
    assert len(overlap_second_in_first_range) == 2
    assert overlap_second_in_first_range[0] == 30
    assert overlap_second_in_first_range[1] == 35

    overlap_minimum_leaves_range = HeatCarrier._overlap(
        TemperatureBus(EnergyQuality(value=50, minimum=[25, 32, 40])),
        TemperatureBus(EnergyQuality(value=30, minimum=30, maximum=35)),
    )
    assert len(overlap_minimum_leaves_range) == 2
    assert sequence_compare(overlap_minimum_leaves_range[0], [30, 32, np.nan])
    assert sequence_compare(overlap_minimum_leaves_range[1], [35, 35, np.nan])


def test_create_overlap_nodes():
    hc = HeatCarrier(label="heat", temperature_levels=[50])

    assert len(hc.inbound_interfaces) == 1
    assert len(hc.outbound_interfaces) == 1

    nodes1 = [
        TemperatureBus(EnergyQuality(value=50, minimum=[25, 32])),
        TemperatureBus(EnergyQuality(value=70)),
    ]
    nodes2 = [
        TemperatureBus(EnergyQuality(value=35, minimum=25)),
        TemperatureBus(EnergyQuality(value=30)),
        TemperatureBus(EnergyQuality(value=50, maximum=[60, 65])),
    ]

    hc._create_overlap_nodes(nodes1, nodes2)

    # preset: 50
    # nodes 1 / nodes 2 | 25 <= T     | == 30 | T <= [60, 65]
    # --------------------------------------------------------
    # [25, 32] <= T     | [25, 32] <= | == 30 | T <= [60, 65]
    #                   | (no ul)     |       | (no ul, again)
    # == 70             | == 70       |       |

    expected_levels = [
        50,  # preset
        [25, 32],  # 1.1/2.1
        sys.float_info.max,  # 1.1 / 2.1 and 1.1 / 2.3
        [30, np.nan],  # 1.1 / 2.2
        [60, 65],  # 1.1 / 2.3
        70,  # 1.2 / 2.1
    ]

    assert len(hc.inbound_interfaces) == 6
    assert len(hc.outbound_interfaces) == 6

    assert (
        hc.inbound_interfaces[TemperatureBus]
        == hc.outbound_interfaces[TemperatureBus]
    )

    for bus in hc.inbound_interfaces[TemperatureBus]:
        assert 1 == sum(sequence_compare(
            bus.energy_quality.value, level, function=np.allclose
        ) for level in expected_levels)





def test_nodes_to_connect():
    temperatures = [-10, 10, 20, [35, 36], 75]
    hc = HeatCarrier(label="heat", temperature_levels=temperatures)

    ntc_33 = hc.nodes_to_connect(TemperatureBus(temperature=33))
    assert len(ntc_33) == 0

    ntc_9_35 = hc.nodes_to_connect(TemperatureBus(
        temperature=EnergyQuality(value=None, minimum=9, maximum=35),
    ))

    ntc_35 = hc.nodes_to_connect(TemperatureBus(temperature=35))
    assert len(ntc_35) == 1
    assert_every_element_is_same(ntc_35[0].temperature, [35, 36])

    ntc_9_35 = hc.nodes_to_connect(TemperatureBus(
        temperature=EnergyQuality(value=None, minimum=9, maximum=35),
    ))

    assert len(ntc_9_35) == 3
    assert ntc_9_35[0].temperature == 10
    assert ntc_9_35[1].temperature == 20
    assert_every_element_is_same(ntc_9_35[2].temperature, [35, 36])
