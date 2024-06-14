"""Room heating technologies."""

from oemof.solph import Bus, Flow
from oemof.solph.components import Source, Sink, Converter

from .._abstract_component import AbstractSolphRepresentation
from .._data_handler import TimeseriesType
from ..carriers import HeatCarrier
from ._abstract_demand import AbstractDemand
from ._abstract_fixed_temperature import AbstractFixedTemperature


class FixedTemperatureHeating(
    AbstractDemand, AbstractSolphRepresentation, AbstractFixedTemperature
):
    """
    Space heating with a fixed flow and return temperature.

    Takes energy from the flow temperature level and returns energy at the lower return
    temperature level.

      (Q(T2))
              ↘
              [heater1,2] ───→ (Qdemand)
              ↙
      (Q(T1))


    Functionality: Demands contain time series of energy that is needed.
        The heat demand automatically connects to its corresponding
        heat  carrier. A name identifying the demand has to be given that
        is unique for the location, because multiple demands of one type
        can exist for one location. Also, the heat demand needs a
        specified temperature level.

    Procedure: Create a simple heat demand by doing the following:

            house_1.add(demands.FixedTemperatureHeat(
                flow_temperature=30, # in °C
                return_temperature=20, # in °C
                time_series=[50]))

    Notice: While energy from electricity and the gaseous carriers is
     just consumed, heat demands have a returning energy flow.
    """

    def __init__(
        self,
        name: str,
        flow_temperature: float,
        return_temperature: float,
        time_series,
    ):

        super().__init__(name=name)

        if not flow_temperature > return_temperature:
            raise ValueError("Flow must be higher than return temperature")

        self.flow_temperature = flow_temperature
        self.return_temperature = return_temperature

        self._time_series = time_series

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        carrier = self.location.get_carrier(HeatCarrier)

        if self.flow_temperature not in carrier.levels:
            raise ValueError("Flow temperature must be a temperature level")

        if self.return_temperature not in carrier.levels:
            raise ValueError("Return temperature must be a temperature level")

        temperature_ratio = 0
        inputs = {}
        outputs = {}
        conversion_factors = {}

        output = self.create_solph_node(
            label="output",
            node_type=Bus,
        )
        outputs[output] = Flow()

        inputs[carrier.level_nodes[self.flow_temperature]] = Flow()
        outputs[carrier.level_nodes[self.return_temperature]] = Flow()

        temperature_ratio = (self.return_temperature - carrier.reference) / (
            self.flow_temperature - carrier.reference
        )
        conversion_factors = {
            carrier.level_nodes[self.flow_temperature]: 1,
            output: 1 - temperature_ratio,
            carrier.level_nodes[self.return_temperature]: temperature_ratio,
        }

        self.create_solph_node(
            label="heat_exchanger",
            node_type=Converter,
            inputs=inputs,
            outputs=outputs,
            conversion_factors=conversion_factors,
        )

        self.create_solph_node(
            label="sink",
            node_type=Sink,
            inputs={
                output: Flow(
                    nominal_value=1,
                    fix=self._solph_model.data.get_timeseries(
                        self._time_series, kind=TimeseriesType.INTERVAL
                    ),
                )
            },
        )
