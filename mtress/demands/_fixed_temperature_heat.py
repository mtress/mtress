"""Room heating technologies."""


from mtress import carriers
from oemof import solph

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

    """

    def __init__(self, flow_temperature: float, return_temperature: float, time_series):
        """
        Initialize space heater.

        :param flow_temperature: Flow temperature
        :param return_temperature: Return temperature
        """
        super().__init__()

        if not flow_temperature > return_temperature:
            raise ValueError("Flow must be higher than return temperature")

        carrier = self.location.get_carrier(Heat)

        if flow_temperature not in carrier.temperature_levels:
            raise ValueError("Flow temperature must be a temperature level")

        if (
            return_temperature not in carrier.temperature_levels
            and return_temperature != carrier.reference_temperature
        ):
            raise ValueError(
                "Return must be a temperature level or the reference temperature"
            )

        self.flow_temperature = flow_temperature
        self.return_temperature = return_temperature

        self._time_series = time_series

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        carrier = self.location.get_carrier(Heat)

        if self.return_temperature == carrier.reference_temperature:
            # If the return temperature is the reference temperature we just take the
            # energy from the appropriate level
            output = self._solph_model.add_solph_component(
                mtress_component=self,
                label="output",
                solph_component=solph.Bus,
                inputs={carrier.outputs[self.flow_temperature]: solph.Flow()},
            )
        else:
            temperature_ratio = (
                self.return_temperature - carrier.reference_temperature
            ) / (self.flow_temperature - carrier.reference_temperature)

            output = self._solph_model.add_solph_component(
                mtress_component=self,
                label="output",
                solph_component=solph.Bus,
            )

            self._solph_model.add_solph_component(
                mtress_component=self,
                label="heat_exchanger",
                inputs={
                    carrier.outputs[self.flow_temperature]: solph.Flow(),
                },
                outputs={
                    carrier.outputs[self.return_temperature]: solph.Flow(),
                    output: solph.Flow(),
                },
                conversion_factors={
                    carrier.outputs[self.flow_temperature]: 1,
                    output: 1 - temperature_ratio,
                    carrier.outputs[self.return_temperature]: temperature_ratio,
                },
            )

        self._solph_model.add_solph_component(
            mtress_component=self,
            label="sink",
            inputs={
                output: solph.Flow(
                    nominal_value=1,
                    fix=self._solph_model.data.get_timeseries(self._time_series),
                )
            },
        )
