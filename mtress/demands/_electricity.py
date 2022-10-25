"""Electricity energy carrier."""

from numbers import Number
from collections.abc import Sequence
from oemof import solph

from ..carriers import Electricity as ElectricityCarrier
from ._abstract_demand import AbstractDemand


class Electricity(AbstractDemand):
    """Class representing an electricity demand."""

    def __init__(self, name: str, time_series: Sequence[Number]):
        """Initialize heat energy carrier and add components."""
        super().__init__(name)
        self._time_series = time_series
        self.input = None

    def build(self):
        electricity_carrier = self.location.get_carrier(ElectricityCarrier)

        self.location.add_demand(self)

        self.input = bus = solph.Bus(
            label=self._generate_label("input"),
            inputs={electricity_carrier.distribution: solph.Flow()},
        )
        sink = solph.Sink(
            label=self._generate_label("sink"),
            inputs={bus: solph.Flow(
                nominal_value=1,
                fix=self._time_series
            )},
        )

        # TODO: categorize out flow

        self.location.energy_system.add(bus, sink)
