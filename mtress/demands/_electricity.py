"""Electricity energy demand."""


from oemof.solph import Bus, Flow
from oemof.solph.components import Sink

from .._abstract_component import AbstractSolphComponent
from ..carriers import Electricity as ElectricityCarrier
from ._abstract_demand import AbstractDemand


class Electricity(AbstractDemand, AbstractSolphComponent):
    """
    Class representing an electricity demand.

    Functionality: Demands contain time series of energy that is needed.
        The electricity demand automatically connects to its corresponding
        electricity  carrier. A name identifying the demand has
        to be given that is unique for the location, because multiple
        demands of one type can exist for one location.

    Procedure: Create a simple electricity demand by doing the following:

            demands.Electricity(location=house_1, time_series=[0, 0.5, 9])

    Notice: The different types of demands have different complexity:
        Electricity demand does not need any further specification,
        heat and gas demand need a specified temperature or pressure
        level, respectively. Further, energy from electricity and the
        gaseous carriers is just consumed, heat demands have a returning
        energy flow.
    """

    def __init__(self, time_series):
        """Initialize heat energy carrier and add components."""
        super().__init__()
        self._time_series = time_series
        self.input = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        electricity_carrier = self.location.get_carrier(ElectricityCarrier)

        bus = self._solph_model.add_solph_component(
            mtress_component=self,
            label="input",
            solph_component=Bus,
            inputs={electricity_carrier.distribution: Flow()},
        )

        self._solph_model.add_solph_component(
            mtress_component=self,
            label="sink",
            solph_component=Sink,
            inputs={
                bus: Flow(
                    nominal_value=1,
                    fix=self._solph_model.data.get_timeseries(self._time_series),
                )
            },
        )

        # TODO: categorize out flow
