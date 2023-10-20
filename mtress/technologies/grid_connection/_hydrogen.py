from typing import Optional


from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Sink, Source
from mtress.carriers import GasCarrier, HYDROGEN
from mtress._abstract_component import AbstractSolphRepresentation
from ._abstract_gas_grid_connection import  AbstractGasGridConnection
from ..._data_handler import TimeseriesSpecifier

class HydrogenGridConnection(AbstractGasGridConnection, AbstractSolphRepresentation):
    """
    Hydrogen grid connection depicts the hydrogen distribution pipelines at specific
    pressure level. Export to the grid is possible with restriction based on max
    injection flow rate allowable at the given time step.

    """

    def __init__(
        self,
        h2_flow_limit: TimeseriesSpecifier,
        grid_pressure: float,
        working_rate: Optional[float] = None,
        demand_rate: Optional[float] = 0,
        revenue: float = 0,

    ):
        """
        Initialize HydrogenGridConnection instance.

        :param h2_flow_limit: Time series of the max hydrogen flow limit
                              (in kg/timestep).
        :param grid_pressure: Pressure level of the H2 Pipeline.
        :param working_rate: Working rate (€/kg H2)
        :param demand_rate: Demand rate
        :param revenue: Revenue that can be earned per kg H2 injection (€/kg H2).

        """
        super().__init__(
            grid_pressure=grid_pressure,
            working_rate=working_rate,
            demand_rate=demand_rate,
            revenue=revenue,
        )

        self.h2_flow_limit = h2_flow_limit

    def build_core(self):

        gas_carrier = self.location.get_carrier(GasCarrier)
        surrounding_levels = gas_carrier.get_surrounding_levels(self.grid_pressure)

        _,pressure = surrounding_levels[HYDROGEN]

        if pressure not in gas_carrier.pressures[HYDROGEN]:
            raise ValueError("Pressure must be a valid input_pressure level")

        b_grid_export = self.create_solph_node(
            label=f"grid_export_{pressure:.0f}",
            node_type=Bus,
            inputs={gas_carrier.outputs[HYDROGEN][pressure]: Flow(
                variable_costs=self.revenue,
                nominal_value=1,
                max=self._solph_model.data.get_timeseries(self.h2_flow_limit),

            )},
        )

        import_pressure, _ = surrounding_levels[HYDROGEN]

        b_grid_import = self.create_solph_node(
            label=f"grid_import_{import_pressure:.0f}",
            node_type=Bus,
            outputs={gas_carrier.inputs[HYDROGEN][import_pressure]: Flow()},
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
