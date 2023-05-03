"""Hydrogen Demand"""

from oemof.solph import Bus, Flow
from oemof.solph.components import Sink, Transformer
from .._data_handler import TimeseriesSpecifier
from .._abstract_component import AbstractSolphComponent
from ..carriers import Hydrogen
from ._abstract_demand import AbstractDemand

class Hydrogen(AbstractDemand, AbstractSolphComponent):
    """
    Class representing a hydrogen demand

    Functionality: Demands contain time series of energy that is needed.
    The hydrogen demand automatically connects to its corresponding
    hydrogen carrier. A name identifying the demand has
    to be given that is unique for the location, because multiple
    demands of one type can exist for one location.

    Procedure: Create a hydrogen demand with specified pressure level by doing the following:

            demands.Hydrogen(location= house_1, time_series=[0, 0.5, 9], pressure=30)

    Notice: The different types of demands have different complexity:
    Electricity demand does not need any further specification,
    heat and gas demand need a specified temperature or pressure
    level, respectively. Further, energy from electricity and the
    gaseous carriers is just consumed, heat demands have a returning
    energy flow.

    """

    def __init__(self, name: str, time_series: TimeseriesSpecifier, pressure: float):
        """Initialize hydrogen energy carrier and add components."""

        super().__init__(name)

        self._time_series = time_series
        self.pressure = pressure


    def build_core(self):
        """Build core structure of oemof.solph representation."""

        hydrogen_carrier = self.location.get_carrier(Hydrogen)
        _,pressure = hydrogen_carrier.get_surrounding_levels(self.pressure)

        if pressure not in hydrogen_carrier.pressure_levels:
            raise ValueError("Pressure must be a valid pressure level")

        bus = self._solph_model.add_solph_component(
            mtress_component=self,
            label="input",
            solph_component=Bus,
            inputs={hydrogen_carrier.outputs[self.pressure]: Flow()},
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