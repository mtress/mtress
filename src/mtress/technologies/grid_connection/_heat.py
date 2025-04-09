"""Heat grid connection."""

from __future__ import annotations
from typing import Optional

from oemof.solph import Bus, Flow
from oemof.solph.components import Source, Sink, Converter

from mtress._abstract_component import AbstractSolphRepresentation
from mtress._data_handler import TimeseriesSpecifier, TimeseriesType
from mtress.carriers import HeatCarrier
from ._abstract_grid_connection import AbstractGridConnection


class HeatGridConnection(AbstractGridConnection, AbstractSolphRepresentation):

    def __init__(
        self,
        maximum_working_temperature: float,
        minimum_working_temperature: float,
        working_rate: Optional[TimeseriesSpecifier] = 0,
        revenue: Optional[TimeseriesSpecifier] = None,
        grid_import_limit: Optional[float] = None,
        grid_export_limit: Optional[float] = None,
    ) -> None:
        """
        Initialize HeatGridConnection
        :param maximum_working_temperature: Flow temperature (°C) of the grid
        :param minimum_working_temperature: Return temperature (°C) of the grid
        :param working_rate: Working price of heat in currency/Wh
        :param revenue: Revenue of the heat export to grid in currency/Wh
        :param grid_import_limit: limits the grid's imports (in W)
        :param grid_export_limit: limits the grid's exports (in W)
        """
        super().__init__()

        self.working_rate = working_rate
        self.revenue = revenue
        self.maximum_working_temperature = maximum_working_temperature
        self.minimum_working_temperature = minimum_working_temperature
        self.grid_import_limit = grid_import_limit
        self.grid_export_limit = grid_export_limit

    def build_core(self):

        heat_carrier = self.location.get_carrier(HeatCarrier)

        input = self.create_solph_node(
            label="input",
            node_type=Bus,
        )

        in_levels = sorted(
            heat_carrier.get_levels_between(
                self.minimum_working_temperature,
                self.maximum_working_temperature,
            ),
            reverse=True,
        )

        for temperature in in_levels[:-1]:
            return_t = in_levels[in_levels.index(temperature) + 1]

            inputs_source = {}
            outputs_source = {}
            convert_source = {}

            inputs_source[input] = Flow(nominal_value=self.grid_import_limit)
            outputs_source[heat_carrier.level_nodes[temperature]] = Flow()
            inputs_source[heat_carrier.level_nodes[return_t]] = Flow()

            convert_source = {
                heat_carrier.level_nodes[temperature]: 1,
                input: (temperature - return_t)
                * heat_carrier.specific_heat_capacity,
                heat_carrier.level_nodes[return_t]: 1,
            }

            self.create_solph_node(
                label=f"T_{temperature}_source",
                node_type=Converter,
                inputs=inputs_source,
                outputs=outputs_source,
                conversion_factors=convert_source,
            )

        self.create_solph_node(
            label="Source",
            node_type=Source,
            outputs={
                input: Flow(
                    variable_costs=self._solph_model.data.get_timeseries(
                        self.working_rate,
                        kind=TimeseriesType.INTERVAL,
                    )
                )
            },
        )

        if self.revenue is not None:

            output = self.create_solph_node(
                label="output",
                node_type=Bus,
            )

            for temperature in in_levels[:-1]:
                return_t = in_levels[in_levels.index(temperature) + 1]

                inputs_sink = {}
                outputs_sink = {}
                convert_sink = {}

                outputs_sink[output] = Flow(
                    nominal_value=self.grid_import_limit
                )
                inputs_sink[heat_carrier.level_nodes[temperature]] = Flow()
                outputs_sink[heat_carrier.level_nodes[return_t]] = Flow()

                convert_source = {
                    heat_carrier.level_nodes[temperature]: 1,
                    output: (temperature - return_t)
                    * heat_carrier.specific_heat_capacity,
                    heat_carrier.level_nodes[return_t]: 1,
                }

                self.create_solph_node(
                    label=f"T_{temperature}_sink",
                    node_type=Converter,
                    inputs=inputs_sink,
                    outputs=outputs_sink,
                    conversion_factors=convert_sink,
                )

            self.create_solph_node(
                label="Sink",
                node_type=Sink,
                inputs={
                    output: Flow(
                        variable_costs=-self._solph_model.data.get_timeseries(
                            self.revenue,
                            kind=TimeseriesType.INTERVAL,
                        )
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
