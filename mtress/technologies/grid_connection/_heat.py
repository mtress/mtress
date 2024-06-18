"""Heat grid connection."""

from typing import Optional

from oemof.solph import Bus, Flow, Source

from mtress.carriers import HeatCarrier
from mtress._abstract_component import AbstractSolphRepresentation
from ._abstract_grid_connection import AbstractGridConnection


class HeatGridConnection(AbstractGridConnection, AbstractSolphRepresentation):
    def __init__(
        self,
        working_rate: Optional[float] = None,
    ) -> None:
        super().__init__()

        self.working_rate = working_rate

    def build_core(self):
        heat_carrier = self.location.get_carrier(HeatCarrier)

        for target_temperature in heat_carrier.temperature_levels:
            level_bus = self.create_solph_node(
                label=f"heat_grid_in_{target_temperature:.0f}",
                node_type=Bus,
                outputs={heat_carrier.level_nodes[target_temperature]: Flow()},
            )

            if self.working_rate is not None:
                self.create_solph_node(
                    label="source_import",
                    node_type=Source,
                    outputs={
                        level_bus: Flow(
                            variable_costs=self.working_rate,
                        )
                    },
                )
