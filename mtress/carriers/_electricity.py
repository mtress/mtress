"""Electricity energy carrier."""


from typing import Optional

from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Sink, Source

from .._abstract_component import AbstractSolphComponent
from ._abstract_carrier import AbstractCarrier


class Electricity(AbstractCarrier, AbstractSolphComponent):
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

            house_1.add_carrier(
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
        """Build solph components."""
        self.distribution = b_dist = self._solph_model.add_solph_component(
            mtress_component=self,
            label="distribution",
            solph_component=Bus,
        )

        self.production = b_prod = self._solph_model.add_solph_component(
            mtress_component=self,
            label="production",
            solph_component=Bus,
            outputs={b_dist: Flow()},
        )

        if self.grid_connection:
            b_grid_export = self._solph_model.add_solph_component(
                mtress_component=self,
                label="grid_export",
                solph_component=Bus,
                inputs={b_prod: Flow()},
            )

            self._solph_model.add_solph_component(
                mtress_component=self,
                label="sink_export",
                solph_component=Sink,
                inputs={b_grid_export: Flow()},
                # TODO: Add revenues
                # Is this the correct place for revenues? Or should they be an option
                # for the generating technologies?
            )

            b_grid_import = self._solph_model.add_solph_component(
                mtress_component=self,
                label="grid_import",
                solph_component=Bus,
                outputs={b_dist: Flow()},
            )

            # (unidirectional) grid connection
            # RLM customer for district and larger buildings
            self._solph_model.add_solph_component(
                mtress_component=self,
                label="source_import",
                solph_component=Source,
                outputs={
                    b_grid_import: Flow(
                        variable_costs=self.working_rate,
                        investment=Investment(ep_costs=self.demand_rate),
                    )
                },
            )

        # TODO: Categorize flows
