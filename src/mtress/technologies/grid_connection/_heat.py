"""Heat grid connection."""

from __future__ import annotations
from typing import Optional

from oemof.solph import Bus, Flow
from oemof.solph.components import Source, Sink

from mtress._abstract_component import AbstractSolphRepresentation
from mtress._data_handler import TimeseriesSpecifier, TimeseriesType
from mtress.carriers import HeatCarrier
from ._abstract_grid_connection import AbstractGridConnection


class HeatGridConnection(AbstractGridConnection, AbstractSolphRepresentation):

    def __init__(
        self,
        maximum_working_temperature: float = 0,
        minimum_working_temperature: float = 0,
        working_rate: Optional[TimeseriesSpecifier] = None,
        revenue: Optional[TimeseriesSpecifier] = None,
    ) -> None:
        """
        Initialize HeatGridConnection
        :param maximum_working_temperature: Maximum flow temperature (°C) of the grid
        :param minimum_working_temperature: Minimum return temperature (°C) of the grid
        :param working_rate: Working price of heat in currency/Wh
        :param revenue: Revenue of the heat export to grid in currency/Wh
        """
        super().__init__()

        self.working_rate = working_rate
        self.revenue = revenue
        self.maximum_working_temperature = maximum_working_temperature
        self.minimum_working_temperature = minimum_working_temperature

        # Properties for solph interfaces
        self.level_nodes = {}

    def build_core(self):

        heat_carrier = self.location.get_carrier(HeatCarrier)

        self._bus_flow = _bus_flow = self.create_solph_node(
            label="HeatGrid_flow",
            node_type=Bus,
        )
        self._bus_return = _bus_return = self.create_solph_node(
            label="HeatGrid_return",
            node_type=Bus,
        )
        if self.working_rate is not None:
            self.create_solph_node(
                label="Source",
                node_type=Source,
                outputs={_bus_flow: Flow()},
            )
            self.create_solph_node(
                label="Sink",
                node_type=Sink,
                inputs={_bus_return: Flow()},
            )
        else:
            self.working_rate = 0

        in_levels = heat_carrier.get_levels_between(
            self.minimum_working_temperature, self.maximum_working_temperature
        )

        for temperature in in_levels:
            if temperature == max(in_levels):
                minimum_t = in_levels[in_levels.index(temperature) - 1]
                specific_working_rate = (
                    self.working_rate
                    * heat_carrier.specific_heat_capacity
                    * (temperature - minimum_t)
                )
                self.level_nodes[temperature] = self.create_solph_node(
                    label=f"T_{temperature}",
                    node_type=Bus,
                    inputs={
                        _bus_flow: Flow(
                            variable_costs=self._solph_model.data.get_timeseries(
                                specific_working_rate,
                                kind=TimeseriesType.INTERVAL,
                            )
                        )
                    },
                    outputs={heat_carrier.level_nodes[temperature]: Flow()},
                )
            elif temperature == min(in_levels):
                self.level_nodes[temperature] = self.create_solph_node(
                    label=f"T_{temperature}",
                    node_type=Bus,
                    inputs={heat_carrier.level_nodes[temperature]: Flow()},
                    outputs={_bus_return: Flow()},
                )
            else:
                minimum_t = in_levels[in_levels.index(temperature) - 1]
                specific_working_rate = (
                    self.working_rate
                    * heat_carrier.specific_heat_capacity
                    * (temperature - minimum_t)
                )
                self.level_nodes[temperature] = self.create_solph_node(
                    label=f"T_{temperature}",
                    node_type=Bus,
                    inputs={
                        _bus_flow: Flow(
                            variable_costs=self._solph_model.data.get_timeseries(
                                specific_working_rate,
                                kind=TimeseriesType.INTERVAL,
                            )
                        ),
                        heat_carrier.level_nodes[temperature]: Flow(),
                    },
                    outputs={
                        _bus_return: Flow(),
                        heat_carrier.level_nodes[temperature]: Flow(),
                    },
                )

    def connect(
        self,
        other: HeatGridConnection,
    ):
        for node1_t, node2_t in zip(
            self.level_nodes.values(), other.level_nodes.values()
        ):
            node1_t.inputs[node2_t] = Flow()
            node1_t.outputs[node2_t] = Flow()
