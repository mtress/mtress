"""Heat grid connection."""

from __future__ import annotations
from typing import Optional

from oemof.solph import Bus, Flow
from oemof.solph.components import Source, Sink, Converter
from ...technologies._heater import AbstractHeater

from mtress._abstract_component import AbstractSolphRepresentation
from mtress._data_handler import TimeseriesSpecifier, TimeseriesType
from mtress.carriers import HeatCarrier
from ._abstract_grid_connection import AbstractGridConnection


class HeatGridConnection(AbstractGridConnection, AbstractHeater):

    def __init__(
        self,
        maximum_temperature: float,
        minimum_temperature: float,
        working_rate: Optional[TimeseriesSpecifier] = 0,
        revenue: Optional[TimeseriesSpecifier] = None,
        grid_import_limit: Optional[float] = None,
        grid_export_limit: Optional[float] = None,
    ) -> None:
        """
        Initialize HeatGridConnection
        :param maximum_temperature: Flow temperature (°C) of the grid
        :param minimum_temperature: Return temperature (°C) of the grid
        :param working_rate: Working price of heat in currency/Wh
        :param revenue: Revenue of the heat export to grid in currency/Wh
        :param grid_import_limit: limits the grid's imports (in W)
        :param grid_export_limit: limits the grid's exports (in W)
        """
        super().__init__(
            maximum_temperature=maximum_temperature,
            minimum_temperature=minimum_temperature,
        )

        self.working_rate = working_rate
        self.revenue = revenue
        self.grid_import_limit = grid_import_limit
        self.grid_export_limit = grid_export_limit

    def build_core(self):

        super().build_core()

        self.create_solph_node(
            label="Source",
            node_type=Source,
            outputs={
                self.heat_bus: Flow(
                    nominal_value=self.grid_import_limit,
                    variable_costs=self._solph_model.data.get_timeseries(
                        self.working_rate,
                        kind=TimeseriesType.INTERVAL,
                    ),
                )
            },
        )

        if self.revenue is not None:

            heat_carrier = self.location.get_carrier(HeatCarrier)

            output = self.create_solph_node(
                label="output",
                node_type=Bus,
            )

            out_levels = heat_carrier.get_levels_between(
                self.minimum_temperature, self.maximum_temperature
            )
            in_levels = heat_carrier.get_levels_between(
                out_levels[1], self.maximum_temperature
            )

            for temp_in, temp_out in zip(in_levels, out_levels):
                bus_warm = heat_carrier.level_nodes[temp_in]
                bus_cold = heat_carrier.level_nodes[temp_out]
                self.create_solph_node(
                    label=f"export_{temp_in:.0f}_{temp_out:.0f}",
                    node_type=Converter,
                    inputs={
                        bus_warm: Flow(),
                    },
                    outputs={
                        bus_cold: Flow(),
                        output: Flow(),
                    },
                    conversion_factors={
                        bus_warm: 1,
                        bus_cold: 1,
                        output: (temp_in - temp_out)
                        * heat_carrier.specific_heat_capacity,
                    },
                )

            self.create_solph_node(
                label="Sink",
                node_type=Sink,
                inputs={
                    output: Flow(
                        nominal_value=self.grid_export_limit,
                        variable_costs=-self._solph_model.data.get_timeseries(
                            self.revenue,
                            kind=TimeseriesType.INTERVAL,
                        ),
                    )
                },
            )


class HeatGridInterconnection(
    AbstractGridConnection, AbstractSolphRepresentation
):

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

        heat_carrier = self.location.get_carrier(HeatCarrier)

        in_levels = heat_carrier.get_levels_between(
            self.return_temperature, self.flow_temperature
        )

        for temperature in in_levels:
            self.level_nodes[temperature] = self.create_solph_node(
                label=f"T_{temperature}",
                node_type=Bus,
                inputs={
                    heat_carrier.level_nodes[temperature]: Flow(),
                },
                outputs={
                    heat_carrier.level_nodes[temperature]: Flow(),
                },
            )

    def connect(
        self,
        other: HeatGridInterconnection,
    ):
        for node1_t, node2_t in zip(
            self.level_nodes.values(), other.level_nodes.values()
        ):
            node1_t.inputs[node2_t] = Flow()
            node1_t.outputs[node2_t] = Flow()
