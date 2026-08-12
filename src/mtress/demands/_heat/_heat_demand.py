"""Heat demands."""

from ..._data_handler import TimeseriesSpecifier
from ...components import FixedReturnHeatSink


class HeatDemandFixedReturn(FixedReturnHeatSink):

    def __init__(
        self,
        label,
        *,
        min_flow_temperature: float,
        return_temperature: float,
        time_series: TimeseriesSpecifier,
        specific_heat_capacity: float = 1.161,
        parent_node=None,
        custom_properties=None,
    ):
        super().__init__(
            label,
            min_flow_temperature=min_flow_temperature,
            return_temperature=return_temperature,
            nominal_power=1.0,
            specific_heat_capacity=specific_heat_capacity,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        self._reservoir_flow.fix = time_series
