# -*- coding: utf-8 -*-
"""The solph representation of the MTRESS meta model.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)

SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Tuple

from graphviz import Digraph
import pandas as pd
from oemof.solph import EnergySystem, Model

from ._data_handler import DataHandler

if TYPE_CHECKING:
    from ._abstract_component import AbstractSolphComponent
    from ._meta_model import MetaModel

class SolphModel:
    """Model adapter for MTRESS meta model."""

    def __init__(
        self,
        meta_model: MetaModel,
        timeindex: dict | list | pd.DatetimeIndex,
    ):
        """
        Initialize model.

        :param timeindex:  time index definition for the soph model
        :param locations: configuration dictionary for locations
        """
        self._meta_model = meta_model
        self._solph_components: Dict[Tuple[AbstractSolphComponent, str], object] = {}

        match timeindex:
            case list() as values:
                self.timeindex = pd.DatetimeIndex(values)
            case pd.DatetimeIndex() as idx:
                self.timeindex = idx
            case dict() as params:
                self.timeindex = pd.date_range(**params)
            case _:
                raise ValueError("Don't know how to process timeindex specification")

        self.data = DataHandler(self.timeindex)

        # Registry of solph components
        self._solph_components = {}
        self.energy_system: EnergySystem = EnergySystem(
            timeindex=self.timeindex, infer_last_interval=False
        )
        self.model: Model = None

        # Store a reference to the solph model
        for component in self._meta_model.components:
            component.register_solph_model(self)

    def build_solph_energy_system(self):
        """Build the `oemof.solph` representation of the energy system."""
        for component in self._meta_model.components:
            component.build_core()

        for component in self._meta_model.components:
            component.establish_interconnections()

        # TODO: Add inter-location connections

    def build_solph_model(self):
        """Build the `oemof.solph` representation of the model."""
        self.model = Model(self.energy_system)

        for component in self._meta_model.components:
            component.add_constraints()

    def graph(self, detail: bool = False) -> Digraph:
        """Generate a graph representation of the energy system."""
        graph = Digraph(name="MTRESS model")
        all_edges = set()

        for location in self._meta_model.locations:
            subgraph, edges = location.graph(detail)

            all_edges.update(edges)
            graph.subgraph(subgraph)

        graph.edges(all_edges)
        return graph

    def solve(
        self,
        solver: str = "cbc",
        solve_kwargs: dict = None,
        cmdline_options: dict = None,
    ):
        """Solve generated energy system model."""
        kwargs = {"solver": solver}
        if solve_kwargs is not None:
            kwargs["solve_kwargs"] = solve_kwargs

        if cmdline_options is not None:
            kwargs["cmdline_options"] = cmdline_options

        self.model.solve(**kwargs)

        return self.model
