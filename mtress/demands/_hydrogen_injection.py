"""Hydrogen injection to Natural gas grid"""

import logging

from oemof.solph import Bus, Flow
from oemof.solph.components import Sink
from .._data_handler import TimeseriesSpecifier
from .._abstract_component import AbstractSolphComponent
from ..carriers import Hydrogen as HydrogenCarrier
from ._abstract_demand import AbstractDemand

LOGGER = logging.getLogger(__file__)


class HydrogenInjection(AbstractDemand, AbstractSolphComponent):
    """
     Class representing a hydrogen injection into Natural gas grid

     Functionality:
     Models the injection of hydrogen into the natural gas grid with the upper limit
     given by volume limit  multiplied by the natural gas flow time series. Due to
     current german regulation, upper % vol limit to the h2 injection is restricted
     with 20%, and therefore it will raise a warning in case higher than 20 % vol limit
     is provided by the user. One can still input higher than 20%  vol H2 injection
     depending on the use case.

     Note: It's important to note that this simplified approach does not account for the
     complexities of the gas grid, such as pressure variations, pipeline capacities, gas
     composition (h2 presence already due to injection at other site within the network?),
     detailed safety considerations and engineering constraints, etc. It provides a rough
     estimation of the maximum allowable hydrogen volume based on the h2 injection volume
     limit and the volumetric flow rate of natural gas at the injection point.


    Procedure: Create a HydrogenInjection instance with the required parameters:
     - name: Name.
     - ng_vol_flow: The time series of the natural gas flow rate (in kg/h).
     - pressure: Pressure level of the hydrogen injection into natural gas grid.
     - revenue: Revenue that can be earned per kg H2 injection (€/kg H2).
     - h2_vol_limit: Volume limit of the hydrogen injection into NG grid.
    """

    def __init__(
        self,
        name: str,
        ng_vol_flow: TimeseriesSpecifier,
        pressure: float,
        revenue: float,
        h2_vol_limit: float,
    ):
        super().__init__(name=name)

        self._ng_vol_flow = ng_vol_flow
        self.pressure = pressure
        self.h2_vol_limit = h2_vol_limit
        self.revenue = revenue

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        hydrogen_carrier = self.location.get_carrier(HydrogenCarrier)
        _, pressure = hydrogen_carrier.get_surrounding_levels(self.pressure)

        if pressure not in hydrogen_carrier.pressure_levels:
            raise ValueError("Pressure must be a valid pressure level")

        if self.h2_vol_limit > 20:
            LOGGER.warning(
                "Provided H2 vol. limit is more than 20 %. "
                "Please make sure it is applicable for your use case,"
                " since as per current german regulation it is limited to 20% vol."
            )

        natural_gas_flow = self._solph_model.data.get_timeseries(self._ng_vol_flow)
        max_hydrogen_flow = natural_gas_flow * (self.h2_vol_limit / 100)

        self.create_solph_component(
            label="sink",
            component=Sink,
            inputs={
                hydrogen_carrier.outputs[self.pressure]: Flow(
                    variable_costs=-self.revenue,
                    nominal_value=1,
                    max=max_hydrogen_flow,
                )
            },
        )
