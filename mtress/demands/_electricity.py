"""Electricity energy carrier."""

from oemof import solph

from ..carriers import Electricity as ElectricityCarrier
from ._abstract_demand import AbstractDemand


class Electricity(AbstractDemand):
    """Class representing an electricity demand."""

    def __init__(self, time_series: str, **kwargs):
        """Initialize heat energy carrier and add components."""
        super().__init__(**kwargs)

        electricity_carrier = self.location.get_carrier(ElectricityCarrier)

        self.input = bus = solph.Bus(
            label=self._generate_label("input"),
            inputs={electricity_carrier.distribution: solph.Flow()},
        )
        sink = solph.Sink(
            label=self._generate_label("sink"),
            inputs={bus: solph.Flow(fix=self.meta_model.get_timeseries(time_series))},
        )

        # TODO: categorize out flow

        self.location.energy_system.add(bus, sink)
