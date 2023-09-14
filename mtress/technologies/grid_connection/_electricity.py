"""Electricity grid connection."""

from typing import Optional

from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Sink, Source

from mtress.carriers import Electricity
from mtress._abstract_component import AbstractSolphRepresentation


class ElectricityGridConnection(AbstractSolphRepresentation):
    def __init__(
        self,
        name: str,
        balanced: bool = False,
        working_rate: Optional[float] = None,
        demand_rate: Optional[float] = 0,
    ) -> None:
        super().__init__(name=name)

        self.balanced = balanced

        self.working_rate = working_rate
        self.demand_rate = demand_rate

    def build_core(self):
        electricity_carrier = self.location.get_carrier(Electricity)

        b_grid_export = self.create_solph_node(
            label="grid_export",
            node_type=Bus,
            inputs={electricity_carrier.production: Flow()},
        )

        self.create_solph_node(
            label="sink_export",
            node_type=Sink,
            inputs={b_grid_export: Flow()},
        )

        b_grid_import = self.create_solph_node(
            label="grid_import",
            node_type=Bus,
            outputs={electricity_carrier.distribution: Flow()},
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
