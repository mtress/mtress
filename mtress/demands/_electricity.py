"""Electricity energy carrier."""


from oemof import solph

from .._abstract_component import AbstractSolphComponent
from ..carriers import Electricity as ElectricityCarrier
from ._abstract_demand import AbstractDemand


class Electricity(AbstractDemand, AbstractSolphComponent):
    """Class representing an electricity demand."""

    def __init__(self, time_series):
        """Initialize heat energy carrier and add components."""
        super().__init__()

        self._time_series = time_series

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        electricity_carrier = self.location.get_carrier(ElectricityCarrier)

        bus = self._solph_model.add_solph_component(
            mtress_component=self,
            label="input",
            solph_component=solph.Bus,
            inputs={electricity_carrier.distribution: solph.Flow()},
        )

        self._solph_model.add_solph_component(
            mtress_component=self,
            label="sink",
            solph_component=solph.Sink,
            inputs={
                bus: solph.Flow(
                    nominal_value=1,
                    fix=self._solph_model.data.get_timeseries(self._time_series),
                )
            },
        )

        # TODO: categorize out flow
