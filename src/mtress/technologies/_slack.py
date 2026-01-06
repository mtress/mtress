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

from .._constants import EnergyType


class SlackNode(AbstractTechnology):
    """
    A component that provides sink and source slack nodes.
    Slack nodes are infinte sources of energy.

    Usage:
        1. One may specify only a penalty.
            All flows have the same, specified, penalty.
            NOTE: The SlackNode auto connects to all present carriers.
        2. One may specify a custom penalty for each desired carrier
            in the following format:
            {CarrierClass[AbstractCarrier]: penalty[float]}
            NOTE: SlackNode only connects to stated carriers
    """

    def __init__(self, penalty: float | dict[AbstractCarrier, float] = 1e9):
        """
        Initialize SlackNode component with infinite source and sink.

        :param penalty: assign a cost for each unit of missing / excess
            energy (in any currency) | per carrier
            {CarrierClass[AbstractCarrier]: penalty[float]}
        """
        super().__init__(name=self.__class__.__name__)

        self.penalty = penalty

    def build_core(self):
        """Build oemof solph core structure."""
        super().build_core()

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
                slack_source[node] = Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    },
                    variable_costs=v,
                )
                slack_sink[node] = Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    },
                    variable_costs=v,
                )
            elif k == HeatCarrier:
                heat_carrier = self.location.get_carrier(HeatCarrier)
                for h_node in heat_carrier.level_nodes.values():
                    slack_source[h_node] = Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.HEAT,
                        },
                        variable_costs=v,
                    )
                    slack_sink[h_node] = Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.HEAT,
                        },
                        variable_costs=v,
                    )
            elif k == GasCarrier:
                gas_carrier = self.location.get_carrier(GasCarrier)
                for gas in gas_carrier.distribution.values():
                    gas_nodes = list(gas.values())  # always sorted
                    gas_high = gas_nodes[-1]
                    slack_source[gas_high] = Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.GAS,
                        },
                        variable_costs=v,
                    )

                    gas_low = gas_nodes[0]
                    slack_sink[gas_low] = Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.GAS,
                        },
                        variable_costs=v,
                    )
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
