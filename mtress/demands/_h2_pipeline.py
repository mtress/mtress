"""Hydrogen injection to 100% H2 Pipeline"""

import logging

from oemof.solph import Flow
from oemof.solph.components import Sink

from .._abstract_component import AbstractSolphRepresentation
from .._data_handler import TimeseriesSpecifier
from ..carriers import Hydrogen as HydrogenCarrier
from ._abstract_demand import AbstractDemand

LOGGER = logging.getLogger(__file__)


class HydrogenPipeline(AbstractDemand, AbstractSolphRepresentation):
    """
     Class representing a hydrogen injection into Hydrogen Pipeline.

    Functionality: This models the hydrogen injection into a 100% Hydrogen Pipeline.
    The inclusion of this feature in MTRESS is based on the recognition of various
    government initiatives in several developed countries, including Germany, where
    efforts are being made to establish pipelines dedicated to transporting 100%
    hydrogen. In Germany, there are already existing/in plan pipelines that have been
    repurposed or newly constructed to transport hydrogen exclusively. This
    functionality can be enabled in MTRESS,allowing for the modeling of hydrogen
    injection into such pipelines.
    """

    def __init__(
        self,
        name: str,
        h2_vol_flow: TimeseriesSpecifier,
        revenue: float,
        pressure: float,
    ):
        """
        Create a HydrogenInjection instance.

        :param name: Name of the component.
        :param h2_vol_flow: Time series of the hydrogen flow limit (in kg/h).
        :param pressure: Pressure level of the hydrogen injection in the H2 Pipeline.
        :param revenue: Revenue that can be earned per kg H2 injection (€/kg H2).
        """
        super().__init__(name=name)

        self._h2_vol_flow = h2_vol_flow
        self.pressure = pressure
        self.revenue = revenue

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        hydrogen_carrier = self.location.get_carrier(HydrogenCarrier)
        _, pressure = hydrogen_carrier.get_surrounding_levels(self.pressure)

        if pressure not in hydrogen_carrier.pressure_levels:
            raise ValueError("Pressure must be a valid pressure level")

        self.create_solph_node(
            label="sink",
            node_type=Sink,
            inputs={
                hydrogen_carrier.outputs[self.pressure]: Flow(
                    variable_costs=-self.revenue,
                    nominal_value=1,
                    max=self._solph_model.data.get_timeseries(self._h2_vol_flow, kind="interval"),
                )
            },
        )
