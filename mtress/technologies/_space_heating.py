"""Room heating technologies."""

from oemof import solph

from ..carriers import Heat
from ..demands import SpaceHeating
from ._abstract_technology import AbstractTechnology


class FixedTemperatureHeater(AbstractTechnology):
    """
    Space heating with a fixede flow and return temperature.

    Takes energy from the flow temperature level and returns energy at the lower return
    temperature level.

      (Q(T2))
         │    ↘
         │    [heater1,2] ───→ (Qdemand)
         ↓    ↙
      (Q(T1))

    """

    def __init__(
        self,
        flow_temperature: float,
        return_temperature: float,
        nominal_value: None,
        **kwargs
    ):
        """
        Initialize space heater.

        :param flow_temperature: Flow temperature
        :param return_temperature: Return temperature
        :param nominal_value: Nominal power of the heater
        """
        super().__init__(**kwargs)

        assert (
            flow_temperature > return_temperature
        ), "Flow must be higher than return temperature"

        carrier = self.location.get_carrier(Heat)
        demand = self.location.get_demand(SpaceHeating)

        assert (
            flow_temperature in carrier.temperature_levels
        ), "Flow temperature must be a temperature level"
        assert (
            return_temperature in carrier.temperature_levels
            or return_temperature == carrier.reference_temperature
        ), "Return temperature must be a temperature level or the reference temperature"

        output_flow = (
            solph.Flow()
            if nominal_value is None
            else solph.Flow(nominal_value=nominal_value)
        )

        if return_temperature == carrier.reference_temperature:
            # If the return temperature is the reference temperature we just take the
            # energy from the appropriate level
            heater = solph.Transformer(
                label=self._generate_label("heater"),
                inputs={carrier.outputs[flow_temperature]: solph.Flow()},
                outputs={demand.input: output_flow},
                conversion_factors={
                    carrier.outputs[flow_temperature]: 1,
                    demand.input: 1,
                },
            )
        else:
            temperature_ratio = (return_temperature - carrier.reference_temperature) / (
                flow_temperature - carrier.reference_temperature
            )

            heater = solph.Transformer(
                label=self._generate_label("heater"),
                inputs={carrier.outputs[flow_temperature]: solph.Flow()},
                outputs={
                    carrier.outputs[return_temperature]: solph.Flow(),
                    demand.input: output_flow,
                },
                conversion_factors={
                    carrier.outputs[flow_temperature]: 1,
                    demand.input: 1 - temperature_ratio,
                    carrier.outputs[return_temperature]: temperature_ratio,
                },
            )

        self.location.energy_system.add(heater)
