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

from ..carriers._abstract_carrier import AbstractCarrier
from ..carriers import ElectricityCarrier, HeatCarrier, GasCarrier
from ._abstract_technology import AbstractTechnology


class SlackNode(AbstractTechnology):
    """
    A component that provides sink and source slack nodes.
    Slack nodes are infinte sources of energy.
    The SlackNode component auto connects to all present carrieres.

    Usage:
        1. One may specify only a penalty.
            All flows have the same, specified, penalty.
        2. One may specify a custom penalty for each desired carrier
            in the following format:
            {CarrierClass[AbstractCarrier]: penalty[float]}
            NOTE: for all other carriers a default penalty is applied
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
        elif isinstance(penalty, dict):
            # check for correct dict structure
            if all(
                [
                    issubclass(k, (AbstractCarrier))
                    and isinstance(v, numbers.Real)
                    for k, v in penalty.items()
                ]
            ):
                self.penalty = penalty
                self.penalty_default = 1e9
            else:
                raise ValueError(
                    "Specifiy penalties in the following format: "
                    + "{CarrierClass[AbstractCarrier]: penalty[float]}"
                )

    def try_carrier(self, carrier_type: type) -> AbstractCarrier | None:
        try:
            carrier = self.location.get_carrier(carrier_type)
        except KeyError:
            carrier = None
        return carrier

    def build_core(self):
        """Build oemof solph core structure."""
        # get all carriers
        carriers = self.location._carriers

        # create full penalties dict
        penalties = {}
        if isinstance(self.penalty, dict):
            # check if all specified carriers are available
            if not set(carriers.keys()).issuperset(set(self.penalty.keys())):
                raise ValueError(
                    "You specified penalties for carriers "
                    + "not available within your system!"
                )
            for k in carriers.keys():
                # add specified penalty
                if k in self.penalty:
                    penalties[k] = self.penalty[k]
                # add default penalty for unspecified carrier
                else:
                    penalties[k] = self.penalty_default
        elif isinstance(self.penalty, numbers.Real):
            # set penalty for all carriers
            for k in carriers.keys():
                penalties[k] = self.penalty

        slack_source = {}  # missing energy
        slack_sink = {}  # excess energy

        # collect all carrier nodes
        for k, v in penalties.items():
            # match default carriers
            if k == ElectricityCarrier:
                electricity_carrier = self.location.get_carrier(
                    ElectricityCarrier
                )
                node = electricity_carrier.distribution
                slack_source[node] = Flow(variable_costs=v)
                slack_sink[node] = Flow(variable_costs=v)
            elif k == HeatCarrier:
                heat_carrier = self.location.get_carrier(HeatCarrier)
                for h_node in heat_carrier.level_nodes.values():
                    slack_source[h_node] = Flow(variable_costs=v)
                    slack_sink[h_node] = Flow(variable_costs=v)
            elif k == GasCarrier:
                gas_carrier = self.location.get_carrier(GasCarrier)
                for gas in gas_carrier.distribution.values():
                    gas_nodes = list(gas.values())  # always sorted
                    gas_high = gas_nodes[-1]
                    slack_source[gas_high] = Flow(variable_costs=v)

                    gas_low = gas_nodes[0]
                    slack_sink[gas_low] = Flow(variable_costs=v)
            # match any other carrier
            # NOTE: will connect sink and source to all nodes
            else:
                carrier = self.location.get_carrier(k)
                for node in carrier.solph_nodes:
                    slack_source[node] = Flow(variable_costs=v)
                    slack_sink[node] = Flow(variable_costs=v)

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
