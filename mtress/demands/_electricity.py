"""Electricity energy demand."""

from oemof.solph import Bus, Flow
from oemof.solph.components import Sink

from .._abstract_component import AbstractSolphRepresentation
from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ..carriers import ElectricityCarrier as ElectricityCarrier
from ._abstract_demand import AbstractDemand


class Electricity(AbstractDemand, AbstractSolphRepresentation):
    """
    Class representing an electricity demand.

    Functionality: Demands contain time series (in Wh) of energy that is
        needed. The electricity demand automatically connects to its
        corresponding electricity  carrier. A name identifying the demand
        has to be given that is unique for the location, because multiple
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

    def __init__(self, name: str, time_series: TimeseriesSpecifier):
        """Initialize electricity energy carrier and add components."""
        super().__init__(name=name)
        self._time_series = time_series
        self.input = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        electricity_carrier = self.location.get_carrier(ElectricityCarrier)

        bus = self.create_solph_node(
            label="input",
            node_type=Bus,
            inputs={electricity_carrier.distribution: Flow()},
        )

        self.create_solph_node(
            label="sink",
            node_type=Sink,
            inputs={
                bus: Flow(
                    nominal_value=1,
                    fix=self._solph_model.data.get_timeseries(
                        self._time_series, kind=TimeseriesType.INTERVAL
                    ),
                )
            },
        )

        # TODO: categorize out flow
