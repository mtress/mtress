"""Gas demand."""

from oemof.solph import Bus, Flow
from oemof.solph.components import Sink

from .._constants import EnergyType
from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ..carriers import GasCarrier
from ..physics import Gas
from ._abstract_demand import AbstractDemand


class GasDemand(AbstractDemand):
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
        label,
        *,
        gas_type: Gas,
        pressure: float,
        time_series: TimeseriesSpecifier,
        location=None,
        custom_properties=None,
    ):
        """Initialize gas demand."""
        super().__init__(
            label,
            location=location,
            custom_properties=custom_properties,
        )

        self._time_series = time_series
        self.gas_type = gas_type
        self.pressure = pressure

        self._build_core()

    def _build_core(self):
        """Build core structure of oemof.solph representation."""

        self._input_node = self.subnode(
            Bus,
            local_name="input",
        )

        self.subnode(
            Sink,
            local_name="sink",
            inputs={
                self._input_node: Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.GAS,
                    },
                    nominal_capacity=1,
                    fix=self._time_series,
                ),
            },
        )

        self.inbound_interfaces[EnergyType.GAS] = [self._input_node]

    def establish_interconnections(self):
        if self.parent:
            gas_carrier = self.parent.get_carrier(GasCarrier)
            _, pressure = gas_carrier.get_surrounding_levels(
                self.gas_type, self.pressure
            )

            self._input_node.inputs[
                gas_carrier.distribution[self.gas_type][pressure]
            ] = Flow(
                custom_properties={
                    "unit": "kg/h",
                    "energy_type": EnergyType.GAS,
                }
            )
