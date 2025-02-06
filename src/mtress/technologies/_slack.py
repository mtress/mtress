# -*- coding: utf-8 -*-

"""
Renewable energy source

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Julius Ellermann


SPDX-License-Identifier: MIT
"""

from oemof.solph import Bus, Flow
from oemof.solph.components import Source, Sink

from .._abstract_component import AbstractSolphRepresentation
from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ..carriers import ElectricityCarrier, HeatCarrier, GasCarrier
from ._abstract_technology import AbstractTechnology


class Slack(AbstractTechnology, AbstractSolphRepresentation):
    """A component that provides sink and source slack nodes"""

    def __init__(self, penalty: float = 1e9):
        """
        Initialize slack component with infinite source and sink

        :param penalty: assign a cost for each unit of missing / excess
            energy (in any currency)
        """
        super().__init__(name=self.__class__.__name__)
        self.penalty = penalty

    def build_core(self):
        """Build oemof solph core structure."""
        # get all carriers
        try:
            electricity_carrier = self.location.get_carrier(ElectricityCarrier)
        except KeyError:
            electricity_carrier = None
        try:
            heat_carrier = self.location.get_carrier(HeatCarrier)
        except KeyError:
            heat_carrier = None
        try:
            gas_carrier = self.location.get_carrier(GasCarrier)
        except KeyError:
            gas_carrier = None

        slack_source = {}  # missing energy
        slack_sink = {}  # excess energy

        # collect all nodes to connect to
        # electricity: distribution node
        if electricity_carrier is not None:
            node = electricity_carrier.distribution
            slack_source[node] = Flow(variable_costs=self.penalty)
            slack_sink[node] = Flow(variable_costs=self.penalty)

        # heat: all T_?? nodes
        if heat_carrier is not None:
            for h_node in heat_carrier.level_nodes.values():
                slack_source[h_node] = Flow(variable_costs=self.penalty)
                slack_sink[h_node] = Flow(variable_costs=self.penalty)

        # gas: highest (missing) and lowest (excess) pressure per gas
        if gas_carrier is not None:
            for gas in gas_carrier.distribution.values():
                gas_nodes = list(gas.values())  # always sorted
                gas_high = gas_nodes[-1]
                slack_source[gas_high] = Flow(variable_costs=self.penalty)

                gas_low = gas_nodes[0]
                slack_sink[gas_low] = Flow(variable_costs=self.penalty)

        # create slack nodes
        self.create_solph_node(
            label="missing_energy",
            node_type=Source,
            outputs=slack_source,
        )

        self.create_solph_node(
            label="excess_energy",
            node_type=Sink,
            inputs=slack_sink,
        )
        # TODO: remove missing / excess heat from heat carrier
