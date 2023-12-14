from typing import Optional

from mtress._abstract_component import AbstractComponent


class AbstractGasGridConnection(AbstractComponent):
    """Abstract class to ensure a unified interface.
    :grid_pressure: in bar
    :working_rate: in currency/Wh
    :demand_rate: in currency/Wh
    :revenue: in currency/Wh
    """

    def __init__(
        self,
        *,
        grid_pressure: float,
        working_rate: Optional[float] = None,
        demand_rate: Optional[float] = 0,
        revenue: float = 0,
        **kwargs,
    ):
        super().__init__(name=self.__class__.__name__, **kwargs)

        self.grid_pressure = grid_pressure
        self.working_rate = working_rate
        self.demand_rate = demand_rate
        self.revenue = revenue
