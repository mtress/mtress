"""Electricity energy demand."""

from oemof.solph import Bus, Flow
from oemof.solph.components import Sink

from .._constants import EnergyType
from .._data_handler import TimeseriesSpecifier, TimeseriesType
from .._carriers import ElectricityCarrier as ElectricityCarrier
from ._abstract_demand import AbstractDemand


class Electricity(AbstractDemand):
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

    def __init__(
        self,
        label,
        *,
        time_series: TimeseriesSpecifier,
        location=None,
        custom_properties=None,
    ):
        """Initialize electricity energy carrier and add components."""
        super().__init__(
            label,
            location=location,
            custom_properties=custom_properties,
        )
        self._time_series = time_series

        self._build_core()

    def _build_core(self):

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
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    },
                    nominal_capacity=1,
                    fix=self._time_series,
                )
            },
        )
        self.inbound_interfaces[EnergyType.ELECTRICITY] = [self._input_node]

    def establish_interconnections(self):
        if self.parent:
            electricity_carrier = self.parent.get_carrier(ElectricityCarrier)

            self._input_node.inputs[electricity_carrier.distribution] = Flow(
                custom_properties={
                    "unit": "W",
                    "energy_type": EnergyType.ELECTRICITY,
                }
            )
