# -*- coding: utf-8 -*-

from mtress import demands
from mtress.carriers import HeatCarrier


def assert_heat_exchanger(node, flow_temperature, return_temperature):
    assert len(node.inbound_interfaces) == 1
    assert len(node.inbound_interfaces) == 1
    [flow_node] = node.inbound_interfaces
    assert flow_node.temperature == flow_temperature

    assert len(node.outbound_interfaces) == 1
    [return_node] = node.outbound_interfaces
    assert return_node.temperature == return_temperature

    assert len(node._subnodes) == 5

    assert (
        node._converters[(flow_node, return_node)].conversion_factors[node._demand]
        == abs(flow_temperature - return_temperature)
        * node.specific_heat_capacity
    )


class TestHeatDemand:
    def default_node(self):
        return demands.FixedReturnHeating(
            label="demand",
            min_flow_temperature=40,
            return_temperature=30,
            time_series=[1, 2, 3],
        )

    def test_basic_initialisation(self):
        node = self.default_node()
        assert_heat_exchanger(node, flow_temperature=40, return_temperature=30)


class TestCoolingDemand:
    def default_node(self):
        return demands.FixedReturnCooling(
            label="demand",
            return_temperature=40,
            max_flow_temperature=20,
            time_series=[1, 2, 3],
        )

    def test_basic_initialisation(self):
        node = self.default_node()
        assert_heat_exchanger(node, flow_temperature=20, return_temperature=40)
