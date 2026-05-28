# -*- coding: utf-8 -*-
"""The solph representation of the MTRESS meta model.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)

SPDX-License-Identifier: MIT
"""

from typing import Iterable

import pandas as pd
from oemof import solph

from ._base_mtress_nodes import SubNetwork

from ._data_handler import DataHandler
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
        """Autoconnect all applicable Nodes (of type SubNetwork)."""
        for sn in self._mtress_nodes:
            sn.establish_interconnections()

    def add_constraints(self, model: solph.Model):
        """Add constraints coded into every SubNetwork."""
        for sn in self._mtress_nodes:
            sn.add_constraints(model)

    @property
    def _mtress_nodes(self) -> Iterable[SubNetwork]:
        """Iterator over all SubNetworks."""
        for component in self.nodes:
            if isinstance(component, SubNetwork):
                yield component

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
