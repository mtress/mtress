from typing import Optional
import logging
from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Sink, Source
from mtress.carriers import GasCarrier, HYDROGEN, BIO_METHANE, NATURAL_GAS
from mtress._abstract_component import AbstractSolphRepresentation
from ._abstract_gas_grid_connection import AbstractGasGridConnection
from ..._data_handler import TimeseriesSpecifier

LOGGER = logging.getLogger(__file__)

class NaturalGasGridConnection(AbstractGasGridConnection, AbstractSolphRepresentation):
    """
    Natural gas grid connection depicts the natural gas distribution pipelines at
    specific pressure level. Injection or export of hydrogen, and bio-methane are
    possible. Hydrogen injection usually restricted by the allowable injection
    limit (at certain percentage of natural gas flow in the pipeline).
    Bio-methane injection currently have no restriction.

    Note: Working_rate must be defined to enable natural gas import for your
          energy system.
    """

    def __init__(
            self,
            grid_pressure: float,
            biomethane_injection: Optional[bool] = False,
            h2_injection: Optional[bool] = False,
            ng_flow: Optional[TimeseriesSpecifier] = 0,
            h2_injection_limit: Optional[float] = None,
            working_rate: Optional[float] = None,
            demand_rate: Optional[float] = 0,
            h2_revenue: Optional[float] = 0,
            biomethane_revenue: Optional[float] = 0,

    ):
        """
        Initialize NaturalGasGridConnection instance.

        :param grid_pressure: Pressure level of the H2 Pipeline.
        :param biomethane_injection: Bio-methane injection is possible if set to True,
                                     default to False.
        :param h2_injection: Hydrogen injection is possible if set to True, default
                             to False.
        :param ng_flow: The time series of the natural gas flow rate (in kg/timestep).
        :param h2_injection_limit: H2 injection limit in terms of percentage of natural
                                   gas flow.
        :param working_rate: Working rate (e.g. €/kg H2)
        :param demand_rate: Demand rate
        :param h2_revenue: Revenue that can be earned per kg H2 injection (e.g. €/kg H2).
        :param biomethane_revenue: Revenue that can be earned per kg bio-methane injection
                                   (e.g. €/kg H2).
        """
        super().__init__(
            grid_pressure=grid_pressure,
            working_rate=working_rate,
            demand_rate=demand_rate,
            revenue=biomethane_revenue,
        )

        self.h2_injection = h2_injection
        self.h2_injection_limit = h2_injection_limit
        self.ng_flow = ng_flow
        self.biomethane_injection = biomethane_injection
        self.h2_revenue = h2_revenue

    def build_core(self):

        if self.h2_injection == True:
            if self.h2_injection_limit is None and self.ng_flow == 0:
                raise ValueError("h2_injection_limit and self.ng_flow"
                                 " must be provided to enable hydrogen injection")
            if self.h2_injection > 7:
                LOGGER.warning(
                    "Provided H2 injection limit is more than 7 %."
                    " Please make sure it is applicable for your use case,"
                    " since as per the current regulation it is limited to 20 % vol."
                    " injection i.e., ~ 7 % by energy density as gas flows are given in kg"
                )
            gas_carrier = self.location.get_carrier(GasCarrier)
            if HYDROGEN not in gas_carrier.gas_type:
                raise ValueError("HYDROGEN must be listed in GasCarrier")
            surrounding_levels = gas_carrier.get_surrounding_levels(self.grid_pressure)

            _, pressure = surrounding_levels[HYDROGEN]

            if pressure not in gas_carrier.pressures[HYDROGEN]:
                raise ValueError("Pressure must be a valid input_pressure level")

            natural_gas_flow = self._solph_model.data.get_timeseries(self.ng_flow)
            max_hydrogen_flow = natural_gas_flow * (self.h2_injection_limit / 100)
            b_grid_export_1 = self.create_solph_node(
                label=f"grid_h2_export_{pressure:.0f}",
                node_type=Bus,
                inputs={gas_carrier.outputs[HYDROGEN][pressure]: Flow(
                    variable_costs=self.revenue,
                    nominal_value=1,
                    max=max_hydrogen_flow,
                )},
            )

            self.create_solph_node(
                label="sink_export_H2",
                node_type=Sink,
                inputs={b_grid_export_1: Flow()}
            )

        if self.biomethane_injection == True:
            gas_carrier = self.location.get_carrier(GasCarrier)
            if BIO_METHANE not in gas_carrier.gas_type:
                raise ValueError("BIO_METHANE must be listed in GasCarrier")
            surrounding_levels = gas_carrier.get_surrounding_levels(self.grid_pressure)

            _, pressure = surrounding_levels[BIO_METHANE]

            if pressure not in gas_carrier.pressures[BIO_METHANE]:
                raise ValueError("Pressure must be a valid input_pressure level")

            b_grid_export_2 = self.create_solph_node(
                label=f"grid_biomethane_export_{pressure:.0f}",
                node_type=Bus,
                inputs={gas_carrier.outputs[BIO_METHANE][pressure]: Flow(
                    variable_costs=self.revenue,
                )},
            )

            self.create_solph_node(
                label="sink_export_BM",
                node_type=Sink,
                inputs={b_grid_export_2: Flow()}
            )

        if self.working_rate is not None:
            if self.demand_rate:
                demand_rate = Investment(ep_costs=self.demand_rate)
            else:
                demand_rate = None

            ng_carrier = self.location.get_carrier(GasCarrier)

            if NATURAL_GAS not in ng_carrier.gas_type:
                raise ValueError("NATURAL_GAS must be listed in GasCarrier or if you"
                                 " don't want natural gas import, then remove"
                                 " working_rate variable from NaturalGasGridConnection")
            surrounding_levels = ng_carrier.get_surrounding_levels(self.grid_pressure)

            pressure_level, _ = surrounding_levels[NATURAL_GAS]

            if pressure_level not in ng_carrier.pressures[NATURAL_GAS]:
                raise ValueError("Pressure must be a valid input_pressure level")

            b_grid_import = self.create_solph_node(
                label=f"grid_import_{pressure_level:.0f}",
                node_type=Bus,
                outputs={ng_carrier.inputs[NATURAL_GAS][pressure_level]: Flow()},
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
