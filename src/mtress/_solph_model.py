# -*- coding: utf-8 -*-
"""The solph representation of the MTRESS meta model.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)

SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Tuple

import pandas as pd
from graphviz import Digraph
from oemof.solph import EnergySystem, Model

from ._data_handler import DataHandler

if TYPE_CHECKING:
    from ._abstract_component import AbstractSolphRepresentation
    from ._meta_model import MetaModel

LOGGER = logging.getLogger(__file__)


class SolphModel:
    """Model adapter for MTRESS meta model."""

    def __init__(
        self,
        meta_model: MetaModel,
        timeindex: dict | list | pd.DatetimeIndex,
    ):
        """
        Initialize model.

        :param meta_model: mtress MetaModel
        :param timeindex:  time index definition for the soph model
        """
        self._meta_model = meta_model
        self._solph_representations: Dict[
            Tuple[AbstractSolphRepresentation, str], object
        ] = {}

        match timeindex:
            case list() as values:
                self.timeindex = pd.DatetimeIndex(values)
            case pd.DatetimeIndex() as idx:
                self.timeindex = idx
            case dict() as params:
                self.timeindex = pd.date_range(**params)
            case _:
                raise ValueError(
                    "Don't know how to process timeindex specification"
                )

        self.data = DataHandler(self.timeindex)

        # Registry of solph representations
        self._solph_representations = {}
        self.energy_system: EnergySystem = EnergySystem(
            timeindex=self.timeindex, infer_last_interval=False
        )
        self.model: Model = None

        # Store a reference to the solph model
        for component in self._meta_model.components:
            component.register_solph_model(self)

        self._build_solph_energy_system()

    def _build_solph_energy_system(self):
        """Build the `oemof.solph` representation of the energy system."""
        for component in self._meta_model.components:
            component.build_core()

        for component in self._meta_model.components:
            component.establish_interconnections()

        for connection in self._meta_model.connections:
            connection.source.connect(
                connection.carrier, connection.destination
            )

    def build_solph_model(self):
        """Build the `oemof.solph` representation of the model."""
        self.model = Model(self.energy_system)

        for component in self._meta_model.components:
            component.add_constraints()

    def graph(
        self,
        detail: bool = False,
        flow_results: dict = None,
        flow_color: dict = None,
        colorscheme: dict = None,
    ) -> Digraph:
        """Generate a graph representation of the energy system."""
        graph = Digraph(name="MTRESS model")
        external_edges = set()

        if flow_color is None:
            flow_color = {}

        if colorscheme is None:
            # set to default
            colorscheme = {
                "ElectricityCarrier": "orange",
                "GasCarrier": "steelblue",
                "HeatCarrier": "maroon",
            }

        for location in self._meta_model.locations:
            subgraph, external_edges = location.graph(
                detail, flow_results, flow_color, colorscheme
            )

            external_edges.update(external_edges)
            graph.subgraph(subgraph)

            for edge in external_edges:
                graph.edge(edge[0], edge[1], label=edge[2], color=edge[3])
        return graph

    def graph_series(
        self,
        flow_results: dict,
        step: pd.Timedelta,
        start: pd.Timestamp = None,
        stop: pd.Timestamp = None,
        flow_color: dict = None,
        colorscheme: dict = None,
    ) -> list[Digraph]:
        """
        Wrapper for graph function to generate multiple graphs as a series.
        """
        if start is None:
            # use first entry of time series
            temp_flow = list(flow_results.items())[0][1]
            start = temp_flow.index[0]
        if stop is None:
            # use last entry of time series
            temp_flow = list(flow_results.items())[0][1]
            stop = temp_flow.index[-1]
        current = start
        graphs = []
        while current + step <= stop:
            current_flow = {
                k: v[current : current + step] for k, v in flow_results.items()
            }
            g = self.graph(
                detail=True,
                flow_results=current_flow,
                flow_color=flow_color,
                colorscheme=colorscheme,
            )
            g.attr(
                label=(
                    current.strftime("%Y-%m-%d %X")
                    + " - "
                    + (current + step).strftime("%Y-%m-%d %X")
                )
            )
            graphs.append(g)
            current += step

        return graphs

    def solve(
        self,
        solver: str = "cbc",
        solve_kwargs: dict = None,
        cmdline_options: dict = None,
    ):
        """Solve generated energy system model."""

        if self.model is None:
            LOGGER.info("Building solph model.")
            self.build_solph_model()
        else:
            LOGGER.info("Using solph model built before.")

        kwargs = {"solver": solver}
        if solve_kwargs is not None:
            kwargs["solve_kwargs"] = solve_kwargs

        if cmdline_options is not None:
            kwargs["cmdline_options"] = cmdline_options

        LOGGER.info("Solving the optimisation model.")
        self.model.solve(**kwargs)

        return self.model
