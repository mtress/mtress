# -*- coding: utf-8 -*-
"""The MTRESS flavour of the solph EnergySystem.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)

SPDX-License-Identifier: MIT
"""

from typing import List

import pandas as pd
from oemof import solph
from oemof.network import Node

from ._base_mtress_nodes import (
    AbstractCarrier,
    AbstractGridConnection,
    AbstractTechnology,
    SubNetwork,
)
from ._data_handler import DataHandler
from ._energy_types import TemperatureBus
from ._helpers._visualization import graph_cytoscape, graph_graphviz


class EnergySystem(solph.EnergySystem):
    """EnergySystem with added custom MTRESS functionality.

    After you are done with populating the EnergySystem,
    please call `EnergySystem.establish_interconnections()`.

    After you created a Model from the EnergySystem,
    please call `EnergySystem.add_constraints(Model)` to add constraints.
    """

    def __init__(
        self,
        timeindex: dict | list | pd.DatetimeIndex,
    ) -> None:
        """
        Initialize the Energy System.

        :param timeindex:  time index definition for the soph model
        """
        match timeindex:
            case list() as values:
                timeindex = pd.DatetimeIndex(values)
            case pd.DatetimeIndex() as idx:
                timeindex = idx
            case dict() as params:
                timeindex = pd.date_range(**params)
            case _:
                raise ValueError(
                    "Don't know how to process timeindex specification"
                )

        self.data = DataHandler(timeindex)

        super().__init__(timeindex=timeindex)

    def establish_interconnections(self):
        """Set time index and autoconnect all applicable Nodes."""
        for sn in self._nodes_by_type(TemperatureBus):
            sn.align_timeindex()

        for sn in self._nodes_by_type(AbstractCarrier):
            sn.establish_interconnections()

        for sn in self._nodes_by_type(AbstractTechnology):
            sn.establish_interconnections()

        for sn in self._nodes_by_type(AbstractGridConnection):
            sn.establish_interconnections()

    def add_constraints(self, model: solph.Model):
        """Add constraints coded into every SubNetwork."""
        for sn in self._nodes_by_type(SubNetwork):
            sn.add_constraints(model)

    def _nodes_by_type(
        self,
        node_type,
    ) -> List[Node]:
        # We do not want an iterable although we only iterate,
        # as we add new items while iterating. Thus, we need a snapshot.
        return [n for n in self.nodes if isinstance(n, node_type)]

    def graph(
        self,
        flow_results: dict = None,
        colour_scheme: dict = None,
        path: str = "model.png",
    ):
        graph_graphviz(
            nodes=self.nodes,
            flows=flow_results,
            colour_scheme=colour_scheme,
            path=path,
        )

    def graph_interactive(
        self,
        flow_results: dict = None,
        colour_scheme: dict = None,
    ):
        graph_cytoscape(
            nodes=self.nodes,
            flows=flow_results,
            colour_scheme=colour_scheme,
        )
