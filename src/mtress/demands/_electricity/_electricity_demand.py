"""Electricity energy demand."""

from oemof.solph import Bus, Flow
from oemof.solph.components import Sink

from ..._base_mtress_nodes import AbstractTechnology
from ..._data_handler import TimeseriesSpecifier, TimeseriesType
from ..._energy_types import EnergyType
from ...carriers import ElectricityCarrier as ElectricityCarrier
from ...components import ElectricitySink


class ElectricityDemand(ElectricitySink):

    def __init__(
        self,
        label,
        *,
        time_series: TimeseriesSpecifier,
        parent_node=None,
        custom_properties=None,
    ):
        """Initialize electricity energy carrier and add components."""
        super().__init__(
            label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )
        self._sink_flow.fix = time_series
