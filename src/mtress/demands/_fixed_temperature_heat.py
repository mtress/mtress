"""Room heating technologies."""

from oemof.solph import Bus, Flow
from oemof.solph.components import Converter, Sink, Source

from .._data_handler import TimeseriesType
from ..carriers import HeatCarrier
from ._abstract_demand import AbstractDemand

from .._constants import EnergyType


class AbstractFixedTemperature(AbstractDemand):
    """
    Superclass for heating or coolig with a fixed return temperature.

    Takes energy from the flow temperature level and returns energy at the
    return temperature level.

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
        self,
        name: str,
        flow_temperature: float,
        return_temperature: float,
        time_series,
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
        super().build_core()

        carrier = self.location.get_carrier(HeatCarrier)

        if self.flow_temperature not in carrier.levels:
            raise ValueError("Flow temperature must be a temperature level")

        if self.return_temperature not in carrier.levels:
            raise ValueError("Return temperature must be a temperature level")

        inputs = {}
        outputs = {}
        conversion_factors = {}

        output = self.create_solph_node(
            label="output",
            node_type=Bus,
        )
        outputs[output] = Flow(
            custom_properties={
                "unit": "W",
                "energy_type": EnergyType.HEAT,
            }
        )

        inputs[carrier.level_nodes[self.flow_temperature]] = Flow(
            custom_properties={
                "unit": "kg/h",
                "energy_type": EnergyType.HEAT,
            }
        )
        outputs[carrier.level_nodes[self.return_temperature]] = Flow(
            custom_properties={
                "unit": "kg/h",
                "energy_type": EnergyType.HEAT,
            }
        )

        conversion_factors = {
            carrier.level_nodes[self.flow_temperature]: 1,
            output: (self.flow_temperature - self.return_temperature)
            * carrier.specific_heat_capacity,
            carrier.level_nodes[self.return_temperature]: 1,
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
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    },
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
        super().build_core()

        carrier = self.location.get_carrier(HeatCarrier)

        inputs = {}
        outputs = {}
        conversion_factors = {}

        _, minimum_t = carrier.get_surrounding_levels(
            self.max_flow_temperature
        )

        input = self.create_solph_node(
            label="input",
            node_type=Bus,
        )

        inputs[input] = Flow(
            custom_properties={
                "unit": "W",
                "energy_type": EnergyType.HEAT,
            }
        )

        outputs[carrier.level_nodes[self.return_temperature]] = Flow(
            custom_properties={
                "unit": "kg/h",
                "energy_type": EnergyType.HEAT,
            }
        )
        inputs[carrier.level_nodes[minimum_t]] = Flow(
            custom_properties={
                "unit": "kg/h",
                "energy_type": EnergyType.HEAT,
            }
        )

        conversion_factors = {
            carrier.level_nodes[self.return_temperature]: 1,
            input: carrier.specific_heat_capacity
            * (self.return_temperature - minimum_t),
            carrier.level_nodes[minimum_t]: 1,
        }

        self.create_solph_node(
            label="heat_exchanger",
            node_type=Converter,
            inputs=inputs,
            outputs=outputs,
            conversion_factors=conversion_factors,
        )

        self.create_solph_node(
            label="source",
            node_type=Source,
            outputs={
                input: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    },
                    nominal_value=1,
                    fix=self._solph_model.data.get_timeseries(
                        self._time_series, kind=TimeseriesType.INTERVAL
                    ),
                )
            },
        )
