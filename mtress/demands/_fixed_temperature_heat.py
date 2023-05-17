"""Room heating technologies."""


from oemof.solph import Bus, Flow
from oemof.solph.components import Sink, Transformer

from .._abstract_component import AbstractSolphComponent
from ..carriers import Heat
from ._abstract_demand import AbstractDemand


class FixedTemperatureHeat(AbstractDemand, AbstractSolphComponent):
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
                flow_temperature=30,
                return_temperature=20,
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

        if not flow_temperature > return_temperature:
            raise ValueError("Flow must be higher than return temperature")

        self.flow_temperature = flow_temperature
        self.return_temperature = return_temperature

        self._time_series = time_series

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        carrier = self.location.get_carrier(Heat)

        if self.flow_temperature not in carrier.temperature_levels:
            raise ValueError("Flow temperature must be a temperature level")

        if (
            self.return_temperature not in carrier.temperature_levels
            and self.return_temperature != carrier.reference_temperature
        ):
            raise ValueError(
                "Return must be a temperature level or the reference temperature"
            )

        if self.return_temperature == carrier.reference_temperature:
            # If the return temperature is the reference temperature we just take the
            # energy from the appropriate level
            output = self.create_solph_component(
                label="output",
                component=Bus,
                inputs={carrier.outputs[self.flow_temperature]: Flow()},
            )
        else:
            temperature_ratio = (
                self.return_temperature - carrier.reference_temperature
            ) / (self.flow_temperature - carrier.reference_temperature)

            output = self.create_solph_component(
                label="output",
                component=Bus,
            )

            self.create_solph_component(
                label="heat_exchanger",
                component=Transformer,
                inputs={
                    carrier.outputs[self.flow_temperature]: Flow(),
                },
                outputs={
                    carrier.outputs[self.return_temperature]: Flow(),
                    output: Flow(),
                },
                conversion_factors={
                    carrier.outputs[self.flow_temperature]: 1,
                    output: 1 - temperature_ratio,
                    carrier.outputs[self.return_temperature]: temperature_ratio,
                },
            )

        self.create_solph_component(
            label="sink",
            component=Sink,
            inputs={
                output: Flow(
                    nominal_value=1,
                    fix=self._solph_model.data.get_timeseries(self._time_series),
                )
            },
        )
