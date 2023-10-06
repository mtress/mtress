"""Gas grid connection."""

from typing import Optional

from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Sink, Source

from mtress.carriers import Gas
from mtress._abstract_component import AbstractSolphRepresentation
from ._abstract_grid_connection import AbstractGridConnection


class GasGridConnection(AbstractGridConnection, AbstractSolphRepresentation):
    """
    This class provides gas grid that could be connected to the gas carrier
    if necessary. Pressure level of grid must be defined to be able to connect
    to the gas carrier at given specific pressure level for gas import and
    export.

    Note: Costs of the gas grid supply (working_price and demand_rate) need
    to be specified.

    """

    def __init__(
        self,
        grid_pressure: float,
        working_rate: Optional[float] = None,
        demand_rate: Optional[float] = 0,
    ) -> None:

        """
        Initialized gas grid connection

        :param grid_pressure: Pressure level of the grid
        :param working_rate: Gas price per KWh
        :param demand_rate: demand rate of the gas grid supply
        """
        super().__init__()
        self.grid_pressure = grid_pressure
        self.working_rate = working_rate
        self.demand_rate = demand_rate

    def build_core(self):

        gas_carrier = self.location.get_carrier(Gas)

        pressure,_ = gas_carrier.get_surrounding_levels(self.grid_pressure)

        if pressure not in gas_carrier.pressure_levels:
            raise ValueError("Pressure must be a valid pressure level")

        b_grid_export = self.create_solph_node(
            label=f"grid_export_{pressure:.0f}",
            node_type=Bus,
            inputs={gas_carrier.feed_in[pressure]: Flow()},
        )

        b_grid_import = self.create_solph_node(
            label=f"grid_import_{pressure:.0f}",
            node_type=Bus,
            outputs={gas_carrier.distribution[pressure]: Flow()},
        )

        self.create_solph_node(
            label="sink_export",
            node_type=Sink,
            inputs={b_grid_export: Flow()},
        )

        if self.working_rate is not None:
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



