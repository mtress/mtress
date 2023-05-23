"""Hydrogen injection to Natural gas grid"""

from oemof.solph import Bus, Flow
from oemof.solph.components import Sink
from .._data_handler import TimeseriesSpecifier
from .._abstract_component import AbstractSolphComponent
from ..carriers import Hydrogen as HydrogenCarrier
from ._abstract_demand import AbstractDemand


class HydrogenInjection(AbstractDemand, AbstractSolphComponent):
    """
    Class representing a hydrogen injection into Natural gas grid
    """
    def __init__(self, name: str, time_series: TimeseriesSpecifier, pressure: float, volume_limit: float):
        """Initialize hydrogen energy carrier and add components."""
        super().__init__(name=name)

        self.time_series = time_series
        self.pressure = pressure
        self.volume_limit = volume_limit

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        hydrogen_carrier = self.location.get_carrier(HydrogenCarrier)
        _, pressure = hydrogen_carrier.get_surrounding_levels(self.pressure)

        natural_gas_flow = self._solph_model.data.get_timeseries(self.time_series)
        max_hydrogen_flow = natural_gas_flow * self.volume_limit

        if pressure not in hydrogen_carrier.pressure_levels:
            raise ValueError("Pressure must be a valid pressure level")

        self.create_solph_component(
            label="sink",
            component=Sink,
            inputs={
                hydrogen_carrier.outputs[self.pressure]: Flow(
                    nominal_value=1,
                    max=max_hydrogen_flow,
                )
            },
        )