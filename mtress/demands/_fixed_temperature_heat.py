"""Room heating technologies."""

from numbers import Number
from collections.abc import Sequence
from oemof import solph

from mtress.carriers import Heat
from ._abstract_demand import AbstractDemand


class FixedTemperatureHeat(AbstractDemand):
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

    def __init__(
        self,
        flow_temperature: float,
        return_temperature: float,
        time_series: Sequence[Number]
    ):
        """
        Initialize space heater.

        :param flow_temperature: Flow temperature
        :param return_temperature: Return temperature
        """
        super().__init__()
        self._flow_temperature = flow_temperature
        self._return_temperature = return_temperature
        self._time_series = time_series
        self.output = None

        assert (
            flow_temperature > return_temperature
        ), "Flow must be higher than return temperature"

    def build(self):
        carrier = self.location.get_carrier(Heat)

        assert (
            self._flow_temperature in carrier.temperature_levels
        ), "Flow temperature must be a temperature level"
        assert (
            self._return_temperature in carrier.temperature_levels
            or self._return_temperature == carrier.reference_temperature
        ), (
            "Return temperature must be a temperature level or the reference"
            " temperature"
        )

        self.output = output = solph.Bus(label=self._generate_label("drained_heat"))

        sink = solph.Sink(
            label=self._generate_label("sink"),
            inputs={
                output: solph.Flow(
                    nominal_value=1,
                    fix=self._time_series,
                )
            },
        )

        if self._return_temperature == carrier.reference_temperature:
            # If the return temperature is the reference temperature we just take the
            # energy from the appropriate level
            heater = solph.Transformer(
                label=self._generate_label("heat_exchanger"),
                inputs={carrier.outputs[self._flow_temperature]: solph.Flow()},
                outputs={output: solph.Flow()},
                conversion_factors={
                    carrier.outputs[self._flow_temperature]: 1,
                    output: 1,
                },
            )
        else:
            temperature_ratio = (
                self._return_temperature - carrier.reference_temperature
            ) / (self._flow_temperature - carrier.reference_temperature)

            heater = solph.Transformer(
                label=self._generate_label("heat_exchanger"),
                inputs={carrier.outputs[self._flow_temperature]: solph.Flow()},
                outputs={
                    carrier.outputs[self._return_temperature]: solph.Flow(),
                    output: solph.Flow(),
                },
                conversion_factors={
                    carrier.outputs[self._flow_temperature]: 1,
                    output: 1 - temperature_ratio,
                    carrier.outputs[self._return_temperature]: temperature_ratio,
                },
            )

        self.location.energy_system.add(heater, output, sink)
