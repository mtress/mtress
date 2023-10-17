"""Hydrogen demand."""

from oemof.solph import Bus, Flow
from oemof.solph.components import Sink
from .._data_handler import TimeseriesSpecifier
from .._abstract_component import AbstractSolphRepresentation
from ..carriers import HYDROGEN, GasCarrier
from ._abstract_demand import AbstractDemand


class Hydrogen(AbstractDemand, AbstractSolphRepresentation):
    """
    Class representing a hydrogen demand

    Functionality: Demands contain time series of energy that is needed.
    The hydrogen demand automatically connects to its corresponding
    hydrogen carrier. A name identifying the demand has
    to be given that is unique for the location, because multiple
    demands of one type can exist for one location.

    Notice: The different types of demands have different complexity:
    Electricity demand does not need any further specification,
    heat and gas demand need a specified temperature or pressure
    level, respectively. Further, energy from electricity and the
    gaseous carriers is just consumed, heat demands have a returning
    energy flow.

    """

    def __init__(self, name: str, time_series: TimeseriesSpecifier, pressure: float):
        """Initialize hydrogen energy carrier and add components."""
        super().__init__(name=name)

        self._time_series = time_series
        self.pressure = pressure

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        hydrogen_carrier = self.location.get_carrier(GasCarrier)
        surrounding_levels = hydrogen_carrier.get_surrounding_levels(self.pressure)

        _, pressure = surrounding_levels[HYDROGEN]

        if pressure not in hydrogen_carrier.pressures[HYDROGEN]:
            raise ValueError("Pressure must be a valid input_pressure level")

        h2_bus = self.create_solph_node(
            label="input",
            node_type=Bus,
            inputs={hydrogen_carrier.outputs[HYDROGEN][pressure]: Flow()},
        )

        self.create_solph_node(
            label="sink",
            node_type=Sink,
            inputs={
                h2_bus: Flow(
                    nominal_value=1,
                    fix=self._solph_model.data.get_timeseries(self._time_series),
                )
            },
        )
