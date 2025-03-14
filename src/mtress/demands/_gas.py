"""Gas demand."""

from oemof.solph import Bus, Flow
from oemof.solph.components import Sink

from .._abstract_component import AbstractSolphRepresentation
from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ..carriers import GasCarrier
from ..physics import Gas
from ._abstract_demand import AbstractDemand


class GasDemand(AbstractDemand, AbstractSolphRepresentation):
    """
    Class representing a gas demand

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

    Parameters
    ----------
    gas_type: in kg
    pressure: in bar
    """

    def __init__(
        self,
        name: str,
        gas_type: Gas,
        time_series: TimeseriesSpecifier,
        pressure: float,
    ):
        """Initialize gas demand."""
        super().__init__(name=name)

        self._time_series = time_series
        self.gas_type = gas_type
        self.pressure = pressure

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        gas_carrier = self.location.get_carrier(GasCarrier)
        _, pressure = gas_carrier.get_surrounding_levels(
            self.gas_type, self.pressure
        )

        gas_bus = self.create_solph_node(
            label="input",
            node_type=Bus,
            inputs={gas_carrier.outputs[self.gas_type][pressure]: Flow()},
        )

        self.create_solph_node(
            label="sink",
            node_type=Sink,
            inputs={
                gas_bus: Flow(
                    nominal_value=1,
                    fix=self._solph_model.data.get_timeseries(
                        self._time_series, kind=TimeseriesType.INTERVAL
                    ),
                )
            },
        )
