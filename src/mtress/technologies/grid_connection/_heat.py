"""Heat grid connection."""

from __future__ import annotations
from typing import Optional

from oemof.solph import Bus, Flow
from ...technologies._heat_exchanger import AbstactHeatExchanger

from mtress._data_handler import TimeseriesSpecifier
from mtress.carriers import HeatCarrier
from ._abstract_grid_connection import AbstractGridConnection

from ..._constants import EnergyType


class HeatGridConnection(AbstractGridConnection, AbstactHeatExchanger):

    def __init__(
        self,
        heat_network_temperature: TimeseriesSpecifier,
        maximum_working_temperature: float,
        minimum_working_temperature: float,
        working_rate: Optional[TimeseriesSpecifier] = 0,
        revenue: Optional[TimeseriesSpecifier] = None,
        grid_limit: Optional[float] = None,
    ) -> None:
        """
        Initialize HeatGridConnection
        :param maximum_temperature: Flow temperature (°C) of the grid
        :param minimum_temperature: Return temperature (°C) of the grid
        :param working_rate: Working price of heat in currency/Wh
        :param revenue: Revenue of the heat export to grid in currency/Wh
        :param grid_limit: limits the grid's nominal power (in W)
        """
        super().__init__(
            reservoir_temperature=heat_network_temperature,
            maximum_working_temperature=maximum_working_temperature,
            minimum_working_temperature=minimum_working_temperature,
            nominal_power=grid_limit,
            working_rate=working_rate,
            revenue=revenue,
        )

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()
        super()._build_core()

    def establish_interconnections(self) -> None:

        super()._define_source()
        if self.revenue is not None:
            super()._define_sink()


class HeatGridInterconnection(AbstractGridConnection):

    def __init__(
        self,
        maximum_working_temperature: float,
        minimum_working_temperature: float,
    ) -> None:
        """
        Initialize HeatGridConnection
        :param maximum_working_temperature: Maximum flow temperature (°C)
            of the internal grid
        :param minimum_working_temperature: Minimum return temperature (°C)
            of the internal grid
        """
        super().__init__()

        self.flow_temperature = maximum_working_temperature
        self.return_temperature = minimum_working_temperature

        # Properties for solph interfaces
        self.level_nodes = {}

    def build_core(self):
        super().build_core()

        heat_carrier = self.location.get_carrier(HeatCarrier)

        in_levels = heat_carrier.get_levels_between(
            self.return_temperature, self.flow_temperature
        )

        for temperature in in_levels:
            self.level_nodes[temperature] = self.create_solph_node(
                label=f"T_{temperature}",
                node_type=Bus,
                inputs={
                    heat_carrier.level_nodes[temperature]: Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.HEAT,
                        }
                    ),
                },
                outputs={
                    heat_carrier.level_nodes[temperature]: Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.HEAT,
                        }
                    ),
                },
            )

    def connect(
        self,
        other: HeatGridInterconnection,
    ):
        for node1_t, node2_t in zip(
            self.level_nodes.values(), other.level_nodes.values()
        ):
            node1_t.inputs[node2_t] = Flow(
                custom_properties={
                    "unit": "kg/h",
                    "energy_type": EnergyType.HEAT,
                }
            )
            node1_t.outputs[node2_t] = Flow(
                custom_properties={
                    "unit": "kg/h",
                    "energy_type": EnergyType.HEAT,
                }
            )
