# -*- coding: utf-8 -*-


from collections import deque

import numpy as np

from mtress import demands
from mtress._energy_types import TemperatureBus


def assert_heat_exchanger(node, flow_temperature, return_temperature):
    assert len(node.inbound_interfaces) == 1
    assert len(node.inbound_interfaces) == 1
    [flow_node] = node.inbound_interfaces
    np.testing.assert_almost_equal(flow_node.temperature, flow_temperature)

    assert len(node.outbound_interfaces) == 1
    [return_node] = node.outbound_interfaces
    np.testing.assert_almost_equal(return_node.temperature, return_temperature)


class TestHeatingDemand:
    def default_node(self):
        return demands.SteppedReturnHeating(
            label="demand",
            reservoir_temperature=[12, 15, -3],
            nominal_power=12,
            maximum_working_temperature=92.0,
            minimum_working_temperature=10.0,
            minimum_delta_medium=5.0,
            minimum_delta_reservoir=2.5,
        )

    def test_basic_initialisation(self):
        node = self.default_node()

        return_temperature = np.array([14.5, 17.5, 12.5])

        assert_heat_exchanger(
            node,
            flow_temperature=return_temperature + 5,
            return_temperature=return_temperature,
        )

    def test_create_io_nodes(self):
        node = self.default_node()

        node20 = TemperatureBus(20)
        node30 = TemperatureBus(30)
        node40 = TemperatureBus(40)

        node._create_io_nodes(
            input_nodes=deque(node30, node40),
            output_nodes=deque(node20, node30),
        )

if __name__ == "__main__":
    import networkx as nx
    import matplotlib.pyplot as plt

    from mtress._helpers._visualization import graph_graphviz
    from mtress import EnergySystem, Location

    location = Location("loc")

    node = location.subnode(
        demands.SteppedReturnHeating,
        local_name="stepped heater",
        reservoir_temperature=[12, 15, -3],
        nominal_power=12,
        maximum_working_temperature=92.0,
        minimum_working_temperature=10.0,
        minimum_delta_medium=5.0,
        minimum_delta_reservoir=2.5,
    )

    node20 = TemperatureBus(20, label="20")
    node30 = TemperatureBus(30, label="30")
    node40 = TemperatureBus(40, label="40")
    node50 = TemperatureBus(50, label="50")

    node._create_io_nodes(
        input_nodes=deque([node30, node40, node50]),
        output_nodes=deque([node20, node30, node40]),
    )

    energy_system = EnergySystem(
        timeindex={
            "start": "2022-01-10 00:00:00",
            "end": "2022-01-10 02:00:00",
            "freq": "60min",
        },
    )
    energy_system.add(location)
    energy_system.add(node20, node30, node40, node50)

    graph_graphviz(
        energy_system.nodes,
        path="stepped_cooling_demand.png",
    )
