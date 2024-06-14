"""Room heating technologies."""

from .._abstract_component import AbstractSolphRepresentation
from .._data_handler import TimeseriesType

from ._abstract_demand import AbstractDemand


class AbstractFixedTemperature(AbstractDemand, AbstractSolphRepresentation):
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
