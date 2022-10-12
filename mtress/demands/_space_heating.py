# -*- coding: utf-8 -*-

from numbers import Number
from collections.abc import Sequence
from oemof import solph

from ._abstract_demand import AbstractDemand


class SpaceHeating(AbstractDemand):
    """Class representing a space heating demand."""

    def __init__(self, time_series: Sequence[Number], **kwargs):
        """Initialize heat energy carrier and add components."""
        super().__init__(**kwargs)

        self.location.add_demand(self)

        self.input = bus = solph.Bus(label=self._generate_label("input"))
        sink = solph.Sink(
            label=self._generate_label("sink"),
            inputs={
                bus: solph.Flow(
                    nominal_value=1,
                    fix=time_series,
                )
            },
        )

        # TODO: categorize out flow

        self.location.energy_system.add(bus, sink)
