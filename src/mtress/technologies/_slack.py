# -*- coding: utf-8 -*-

"""
Renewable energy source

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Julius Ellermann


SPDX-License-Identifier: MIT
"""
import numbers

from oemof.solph import Flow
from oemof.solph.components import Source, Sink

from .._abstract_component import AbstractSolphRepresentation
from ..carriers._abstract_carrier import AbstractCarrier
from ..carriers import ElectricityCarrier, HeatCarrier, GasCarrier
from ._abstract_technology import AbstractTechnology


class SlackNode(AbstractTechnology, AbstractSolphRepresentation):
    """
    A component that provides sink and source slack nodes.
    Slack nodes are infinte sources of energy.

    Usage:
        1. One may specify only a penalty.
            The SlackNode component auto connects to all present carrieres.
            All flows have the same, specified, penalty.
        2. One may specify a penalty for each desired carrier
            in the following format:
            {CarrierClass[AbstractCarrier]: penalty[float]}
    """

    def __init__(self, penalty: float | dict[AbstractCarrier, float] = 1e9):
        """
        Initialize SlackNode component with infinite source and sink.

        :param penalty: assign a cost for each unit of missing / excess
            energy (in any currency) | per carrier
            {CarrierClass[AbstractCarrier]: penalty[float]}
        """
        super().__init__(name=self.__class__.__name__)
        if isinstance(penalty, numbers.Real):
            # set same penalty for all present carriers
            self.penalty = penalty
            self.auto_connect = True
        elif isinstance(penalty, dict):
            # check for correct dict structure
            if all(
                issubclass(k, AbstractCarrier) and type(v) == float
                for k, v in penalty.items()
            ):
                self.penalty = penalty
                self.auto_connect = False
            else:
                raise ValueError("Specify a penalty for each carrier!")

    def try_carrier(self, carrier_type: type) -> AbstractCarrier | None:
        try:
            carrier = self.location.get_carrier(carrier_type)
        except KeyError:
            carrier = None
        return carrier

    def build_core(self):
        """Build oemof solph core structure."""
        electricity_carrier = None
        heat_carrier = None
        gas_carrier = None

        if self.auto_connect:
            # get all carriers
            electricity_carrier = self.try_carrier(ElectricityCarrier)
            electricity_penalty = self.penalty
            heat_carrier = self.try_carrier(HeatCarrier)
            heat_penalty = self.penalty
            gas_carrier = self.try_carrier(GasCarrier)
            gas_penalty = self.penalty
        else:
            # get only the specified carriers
            for k, v in self.penalty.items():
                if k == ElectricityCarrier:
                    electricity_carrier = self.try_carrier(ElectricityCarrier)
                    electricity_penalty = v
                elif k == HeatCarrier:
                    heat_carrier = self.try_carrier(HeatCarrier)
                    heat_penalty = v
                elif k == GasCarrier:
                    gas_carrier = self.try_carrier(GasCarrier)
                    gas_penalty = v

        slack_source = {}  # missing energy
        slack_sink = {}  # excess energy

        # collect all nodes to connect to
        # electricity: distribution node
        if electricity_carrier is not None:
            node = electricity_carrier.distribution
            slack_source[node] = Flow(variable_costs=electricity_penalty)
            slack_sink[node] = Flow(variable_costs=electricity_penalty)

        # heat: all T_?? nodes
        if heat_carrier is not None:
            for h_node in heat_carrier.level_nodes.values():
                slack_source[h_node] = Flow(variable_costs=heat_penalty)
                slack_sink[h_node] = Flow(variable_costs=heat_penalty)

        # gas: highest (missing) and lowest (excess) pressure per gas
        if gas_carrier is not None:
            for gas in gas_carrier.distribution.values():
                gas_nodes = list(gas.values())  # always sorted
                gas_high = gas_nodes[-1]
                slack_source[gas_high] = Flow(variable_costs=gas_penalty)

                gas_low = gas_nodes[0]
                slack_sink[gas_low] = Flow(variable_costs=gas_penalty)

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

    def establish_interconnections(self) -> None:
        pass
