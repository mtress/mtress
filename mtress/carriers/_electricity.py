"""Electricity energy carrier."""

from __future__ import annotations

from typing import Optional

from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Sink, Source

from .._abstract_component import AbstractSolphRepresentation
from ._abstract_carrier import AbstractCarrier


class Electricity(AbstractCarrier, AbstractSolphRepresentation):
    """
    Electricity energy carrier.

    Functionality: Electricity connections at a location. This class
        represents a local electricity grid with or without connection
        to the global electricity grid.

        All default busses, sources and sinks are automatically generated
        and interconnected when the carrier is initialized. Automatically
        generated are the following: one bus each for production, distribution,
        export, grid_in (actual grid supply with costs), grid_out (external
        market to sell electricity to) as well as a source (additional
        unidirictional grid connection) and a sink (export).

        Other components and demands might be added to the energy_system by
        their respective classes / functions and are automatically connected
        to their fitting busses by the carrier.

    Procedure: Create a simple electricity carrier by doing the following
        and adding costs to the grid supply.

            house_1.add(
                carriers.Electricity(costs={"working_price": 35, "demand_rate": 0})

    Notice: Costs of the grid supply (working_price and demand_rate) need to
        be specified.

    """

    # TODO: the term demand_rate feels unintuitive; better variable_name for that?
    def __init__(
        self,
        grid_connection: bool = True,
        working_rate: Optional[float] = None,
        demand_rate: Optional[float] = None,
    ):
        """Initialize electricity carrier."""
        super().__init__()

        self.grid_connection = grid_connection

        self.working_rate = working_rate
        self.demand_rate = demand_rate

        # Properties for connection oemof.solph busses
        self.distribution = None
        self.production = None

    def build_core(self):
        """Build solph nodes."""
        self.distribution = b_dist = self.create_solph_node(
            label="distribution",
            node_type=Bus,
        )

        self.production = b_prod = self.create_solph_node(
            label="production",
            node_type=Bus,
            outputs={b_dist: Flow()},
        )

        self.grid_export = b_grid_export = self.create_solph_node(
            label="grid_export",
            node_type=Bus,
            inputs={b_prod: Flow()},
        )

        self.grid_import = b_grid_import = self.create_solph_node(
            label="grid_import",
            node_type=Bus,
            outputs={b_dist: Flow()},
        )

        if self.grid_connection:
            self.create_solph_node(
                label="sink_export",
                node_type=Sink,
                inputs={b_grid_export: Flow()},
                # TODO: Add revenues
                # Is this the correct place for revenues? Or should they be an option
                # for the generating technologies?
            )

            if self.demand_rate:
                demand_rate = Investment(ep_costs=self.demand_rate)
            else:
                demand_rate = None

            # (unidirectional) grid connection
            # RLM customer for district and larger buildings
            self.create_solph_node(
                label="source_import",
                node_type=Source,
                outputs={
                    b_grid_import: Flow(
                        variable_costs=self.working_rate,
                        investment=demand_rate,
                    )
                },
            )

        # TODO: Categorize flows

    def connect(
        self,
        other: Electricity,
    ):
        self.location_link = self.create_solph_node(
            label="location_link",
            node_type=Bus,
            inputs={self.grid_export: Flow()},
            outputs={other.grid_import: Flow()},
        )
