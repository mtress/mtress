# -*- coding: utf-8 -*-

from mtress import demands
from mtress import EnergyType


def assert_heat_exchanger(node, flow_temperature, return_temperature):
    assert node._time_series == [1, 2, 3]
    assert node.flow_temperature == flow_temperature
    assert node.return_temperature == return_temperature

    assert len(node.inbound_interfaces) == 1
    assert len(node.inbound_interfaces[EnergyType.HEAT]) == 1
    [flow_node] = node.inbound_interfaces[EnergyType.HEAT]
    assert flow_node.temperature == flow_temperature

    assert len(node.outbound_interfaces) == 1
    assert len(node.outbound_interfaces[EnergyType.HEAT]) == 1
    [return_node] = node.outbound_interfaces[EnergyType.HEAT]
    assert return_node.temperature == return_temperature

    assert len(node._subnodes) == 4

    assert (
        node._converter.conversion_factors[node._demand]
        == abs(flow_temperature - return_temperature)
        * node.specific_heat_capacity
    )


class TestHeatDemand:
    def default_node(self):
        return demands.FixedTemperatureHeating(
            label="demand",
            min_flow_temperature=40,
            return_temperature=30,
            time_series=[1, 2, 3],
        )

    def test_basic_initialisation(self):
        node = self.default_node()
        assert_heat_exchanger(node, flow_temperature=40, return_temperature=30)

    def test_change_flow(self):
        node = self.default_node()
        node.flow_temperature = 50
        assert_heat_exchanger(node, flow_temperature=50, return_temperature=30)


class TestCoolingDemand:
    def default_node(self):
        return demands.FixedTemperatureCooling(
            label="demand",
            return_temperature=40,
            max_flow_temperature=20,
            time_series=[1, 2, 3],
        )

    def test_basic_initialisation(self):
        node = self.default_node()
        assert_heat_exchanger(node, flow_temperature=20, return_temperature=40)

    def test_change_flow(self):
        node = self.default_node()
        node.flow_temperature = 10
        assert_heat_exchanger(node, flow_temperature=10, return_temperature=40)
