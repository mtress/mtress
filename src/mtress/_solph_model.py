# -*- coding: utf-8 -*-
"""The solph representation of the MTRESS meta model.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)

SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Tuple

import pandas as pd
from dash import Dash, html, dcc, Input, Output, callback
import dash_cytoscape as cyto
import logging
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
        flow_results: dict = None,
        flow_color: dict = None,
        colorscheme: dict = None,
    ) -> None:  # return Dash?
        """
        Generate an interactive graph representation of the energy system.
        """
        # manage coloring
        if flow_color is None:
            flow_color = {}

        if colorscheme is None:
            # set to default
            colorscheme = {
                "ElectricityCarrier": "orange",
                "GasCarrier": "steelblue",
                "HeatCarrier": "maroon",
            }

        nodes_simple, nodes_detail, nodes_result = [], [], []
        # iterate locations
        for location in self._meta_model.locations:
            n_simple, n_detail, n_result = location.graph(
                flow_results,
                flow_color,
                colorscheme,
            )
            nodes_simple += n_simple
            nodes_detail += n_detail
            nodes_result += n_result

        # init dash cytoscape
        cyto.load_extra_layouts()
        app = Dash()

        tabs = [
            dcc.Tab(label="simple", value="simple"),
            dcc.Tab(label="detail", value="detail"),
        ]
        if flow_results != None:
            tabs.append(dcc.Tab(label="results", value="results"))
        app.layout = html.Div(
            [
                dcc.Tabs(
                    id="detail_selector",
                    value="simple",
                    children=tabs,
                ),
                html.Div(id="graph"),
            ]
        )

        @callback(
            Output("graph", "children"), Input("detail_selector", "value")
        )
        def render_graph(tab):
            if tab == "simple":
                n = nodes_simple
            elif tab == "detail":
                n = nodes_detail
            elif tab == "results":
                n = nodes_result

            return html.Div(
                [
                    cyto.Cytoscape(
                        id="mtress_model",
                        layout={"name": "cose-bilkent"},  # cola | klay
                        style={
                            "width": "100%",
                            "height": "calc(100vh - 120px)",
                        },
                        stylesheet=[
                            # Group selectors
                            {
                                "selector": "node",
                                "style": {
                                    "content": "data(label)",
                                    "shape": "cut-rectangle",
                                },
                            },
                            {
                                "selector": "edge",
                                "style": {
                                    "curve-style": "bezier",
                                    "source-arrow-shape": "triangle",
                                    "line-color": "black",
                                    "source-arrow-color": "black",
                                },
                            },
                            # Class selectors
                            # coloring
                            {
                                "selector": "." + colorscheme["HeatCarrier"],
                                "style": {
                                    "line-color": colorscheme["HeatCarrier"],
                                    "source-arrow-color": colorscheme[
                                        "HeatCarrier"
                                    ],
                                },
                            },
                            {
                                "selector": "."
                                + colorscheme["ElectricityCarrier"],
                                "style": {
                                    "line-color": colorscheme[
                                        "ElectricityCarrier"
                                    ],
                                    "source-arrow-color": colorscheme[
                                        "ElectricityCarrier"
                                    ],
                                },
                            },
                            {
                                "selector": "." + colorscheme["GasCarrier"],
                                "style": {
                                    "line-color": colorscheme["GasCarrier"],
                                    "source-arrow-color": colorscheme[
                                        "GasCarrier"
                                    ],
                                },
                            },
                            {
                                "selector": ".inactive",
                                "style": {
                                    "line-color": "lightgrey",
                                    "source-arrow-color": "lightgrey",
                                },
                            },
                            {
                                "selector": ".rainbow",
                                "style": {
                                    "line-fill": "linear-gradient",
                                    "line-gradient-stop-colors": "firebrick darkorange gold chartreuse deepskyblue cornflowerblue darkslateblue",
                                    "source-arrow-color": "firebrick",
                                },
                            },
                            # node shapes
                            {
                                "selector": ".source",
                                "style": {
                                    "shape": "polygon",
                                    "shape-polygon-points": "1, 1, 0.5, -1, -0.5, -1, -1, 1",
                                    "text-valign": "center",
                                    "text-halign": "center",
                                    "width": "label",
                                },
                            },
                            {
                                "selector": ".sink",
                                "style": {
                                    "shape": "polygon",
                                    "shape-polygon-points": "0.5, 1, 1, -1, -1, -1, -0.5, 1",
                                    "text-valign": "center",
                                    "text-halign": "center",
                                    "width": "label",
                                },
                            },
                            {
                                "selector": ".bus",
                                "style": {
                                    "shape": "ellipse",
                                    "text-valign": "center",
                                    "text-halign": "center",
                                    "width": "label",
                                },
                            },
                            {
                                "selector": ".converter",
                                "style": {
                                    "shape": "octagon",
                                    "text-valign": "center",
                                    "text-halign": "center",
                                    "width": "label",
                                },
                            },
                            {
                                "selector": ".storage",
                                "style": {
                                    "shape": "barrel",
                                    "text-valign": "center",
                                    "text-halign": "center",
                                    "width": "label",
                                },
                            },
                            {
                                "selector": ".parent",
                                "style": {
                                    "shape": "round-rectangle",
                                    "text-valign": "top",
                                },
                            },
                        ],
                        elements=n,
                    )
                ]
            )

        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        app.run(debug=False)  # TODO: debug true?

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
