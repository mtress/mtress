"""Room heating technologies."""

from oemof.solph import Bus, Flow
from oemof.solph.components import Source, Sink, Converter

from .._data_handler import TimeseriesType
from ..carriers import HeatCarrier

from .._abstract_component import AbstractSolphRepresentation
from ._abstract_demand import AbstractDemand


class AbstractFixedTemperature(AbstractDemand, AbstractSolphRepresentation):
    """
    Superclass for heating or coolig with a fixed return temperature.

    Takes energy from the flow temperature level and returns energy at the return
    temperature level.

    Functionality: Demands contain time series of energy that is needed.
        The heat demand automatically connects to its corresponding
        heat  carrier. A name identifying the demand has to be given that
        is unique for the location, because multiple demands of one type
        can exist for one location.

    Procedure: Create a simple heat demand by doing the following:

            house_1.add(demands.FixedTemperatureHeat(
                flow_temperature=30, # in °C
                return_temperature=20, # in °C
                time_series=[50]))

    Notice: While energy from electricity and the gaseous carriers is
     just consumed, heat demands have a returning energy flow.
    """

    def __init__(
        self, name: str, flow_temperature: float, return_temperature: float, time_series
    ):
        """
        Initialize space heater.

        :param flow_temperature: Flow temperature
        :param return_temperature: Return temperature
        """
        super().__init__(name=name)

        self.flow_temperature = flow_temperature
        self.return_temperature = return_temperature

        self._time_series = time_series


class FixedTemperatureHeating(AbstractFixedTemperature):
    def __init__(
        self,
        name: str,
        min_flow_temperature: float,
        return_temperature: float,
        time_series,
    ):  
        """
        Heating demand with a fixed return temperature.

        :param min_flow_temperature: minimum temperature
            that can be used for heating 
        :param return_temperature: return temperature
        :param time_series: demand time series (in W)
        """
        super().__init__(
            name=name,
            flow_temperature=min_flow_temperature,
            return_temperature=return_temperature,
            time_series=time_series,
        )

        if not min_flow_temperature > return_temperature:
            raise ValueError("Flow must be higher than return temperature")

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


class FixedTemperatureCooling(AbstractFixedTemperature):
    def __init__(
        self,
        name: str,
        return_temperature: float,
        max_flow_temperature: float,
        time_series,
        flow_temperature: float = None,
    ):
        """
        Cooling demand with a fixed return temperature.

        :param max_flow_temperature: maximum temperature
            that can be used for cooling 
        :param return_temperature: return temperature
        :param time_series: demand time series (in W)
        """
        super().__init__(
            name=name,
            flow_temperature=flow_temperature,
            return_temperature=return_temperature,
            time_series=time_series,
        )

        self.max_flow_temperature = max_flow_temperature

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        carrier = self.location.get_carrier(HeatCarrier)

        temperature_ratio = 0
        inputs = {}
        outputs = {}
        conversion_factors = {}

        _, minimum_t = carrier.get_surrounding_levels(self.max_flow_temperature)

        input = self.create_solph_node(
            label="input",
            node_type=Bus,
        )

        inputs[input] = Flow()

        outputs[carrier.level_nodes[self.return_temperature]] = Flow()
        inputs[carrier.level_nodes[minimum_t]] = Flow()

        temperature_ratio = (minimum_t - carrier.reference) / (
            self.return_temperature - carrier.reference
        )

        conversion_factors = {
            carrier.level_nodes[self.return_temperature]: 1,
            input: 1 - temperature_ratio,
            carrier.level_nodes[minimum_t]: temperature_ratio,
        }

        self.create_solph_node(
            label="heat_exchanger",
            node_type=Converter,
            inputs=inputs,
            outputs=outputs,
            conversion_factors=conversion_factors,
        )

        self.create_solph_node(
            label="Source",
            node_type=Source,
            outputs={
                input: Flow(
                    nominal_value=1,
                    fix=self._solph_model.data.get_timeseries(
                        self._time_series, kind=TimeseriesType.INTERVAL
                    ),
                )
            },
        )
