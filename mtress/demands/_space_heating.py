# -*- coding: utf-8 -*-

from oemof import solph

from ._abstract_demand import AbstractDemand


class SpaceHeating(AbstractDemand):
    """Class representing a space heating demand."""

    def __init__(self, time_series: str, **kwargs):
        """Initialize heat energy carrier and add components."""
        super().__init__(**kwargs)

        self.input = bus = solph.Bus(label=self._generate_label("input"))
        sink = solph.Sink(
            label=self._generate_label("sink"),
            inputs={bus: solph.Flow(fix=self.meta_model.get_timeseries(time_series))},
        )

        # TODO: categorize out flow

        self.location.energy_system.add(bus, sink)
