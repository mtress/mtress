from typing import Optional

from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Sink, Source

from .._abstract_component import AbstractSolphRepresentation
from ._abstract_carrier import AbstractCarrier


class NaturalGas(AbstractCarrier, AbstractSolphRepresentation):
    """
    Natural gas energy carrier.

    Functionality: Natural gas connections at a location. This class
        represents a local natural gas grid with or without connection
        to the global natural gas grid.

        All natural gas flows in MTRESS are given in Nm3. Therefore, the
        calorific values should also be based on Nm3.

        All default busses, sources and sinks are automatically generated
        and interconnected when the carrier is initialized. Automatically
        generated are the following: one bus each for production, distribution,
        export, grid_import (actual grid supply with costs), grid_export (external
        market to sell natural gas to) as well as a source (additional
        uni-dirictional gas grid connection) and a sink (export).

        Other components and demands might be added to the energy_system by
        their respective classes / functions and are automatically connected
        to their fitting busses by the carrier.

    Notice: Costs of the grid supply (working_price and demand_rate) need to
        be specified.

    """

    def __init__(
        self,
        ng_grid_connection: bool = True,
        working_rate: Optional[float] = None,
        revenue_rate: Optional[float] = None,
        demand_rate: Optional[float] = None,
    ):
        """Initialize natural gas carrier."""
        super().__init__()

        self.grid_connection = ng_grid_connection

        self.working_rate = working_rate
        self.revenue_rate = revenue_rate
        self.demand_rate = demand_rate
        # Properties for connection oemof.solph busses
        self.distribution = None
        self.production = None

    def build_core(self):
        """Build solph nodes."""
        self.distribution = b_dist = self.create_solph_node(
            label="gas_distribution",
            node_type=Bus,
        )

        self.production = b_prod = self.create_solph_node(
            label="gas_production",
            node_type=Bus,
            outputs={b_dist: Flow()},
        )

        if self.grid_connection:
            b_grid_export = self.create_solph_node(
                label="gas_export",
                node_type=Bus,
                inputs={b_prod: Flow()},
            )

            self.create_solph_node(
                label="sink_export",
                node_type=Sink,
                inputs={b_grid_export: Flow()},

            )

            b_grid_import = self.create_solph_node(
                label="gas_grid_import",
                node_type=Bus,
                outputs={b_dist: Flow()},
            )

            if self.demand_rate:
                demand_rate = Investment(ep_costs=self.demand_rate)
            else:
                demand_rate = None

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