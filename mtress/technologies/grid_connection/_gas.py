from typing import Optional
import logging
from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Sink, Source
from mtress.carriers import GasCarrier, Gas
from mtress._abstract_component import AbstractSolphRepresentation

LOGGER = logging.getLogger(__file__)

class GasGridConnection(AbstractSolphRepresentation):
    """
    Gas grid connection depicts the natural gas distribution pipelines at
    specific pressure level. Injection or export of hydrogen, and bio-methane are
    possible. Hydrogen injection usually restricted by the allowable injection
    limit (at certain percentage of natural gas flow in the pipeline).
    Bio-methane injection currently have no restriction.

    Note: Working_rate must be defined to enable natural gas import for your
          energy system.
    """
    def __init__(
        self,
        *,
        gas_type: Gas,
        grid_pressure: float,
        working_rate: Optional[float] = None,
        demand_rate: Optional[float] = 0,
        revenue: float = 0,
        **kwargs,
    ):
        """

        """
        super().__init__(**kwargs)
        self.gas_type = gas_type
        self.grid_pressure = grid_pressure
        self.working_rate = working_rate
        self.demand_rate = demand_rate
        self.revenue = revenue

    def build_core(self):
        gas_carrier = self.location.get_carrier(GasCarrier)

        _, pressure_level = gas_carrier.get_surrounding_levels(self.gas_type, self.grid_pressure)

        if self.working_rate is not None:
            if self.demand_rate:
                demand_rate = Investment(ep_costs=self.demand_rate)
            else:
                demand_rate = None

            b_grid_import = self.create_solph_node(
                label=f"grid_import_{pressure_level:.0f}",
                node_type=Bus,
                outputs={gas_carrier.inputs[self.gas_type][pressure_level]: Flow()},
            )

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
