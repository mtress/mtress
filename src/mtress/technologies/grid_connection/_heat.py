"""Heat grid connection."""

from __future__ import annotations
from typing import Optional

from oemof.solph import Bus, Flow
from oemof.solph.components import Converter, Source

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
        :param revenue: Revenue of the gas export to grid in currency/Wh
        """
        super().__init__()

        self.working_rate = working_rate
        self.revenue = revenue
        self.maximum_working_temperature = maximum_working_temperature
        self.minimum_working_temperature = minimum_working_temperature
        self._bus_source = None
        self._bus_export = None

    def build_core(self):

        heat_carrier = self.location.get_carrier(HeatCarrier)

        self._bus_source = _bus_source = self.create_solph_node(
            label="grid_import",
            node_type=Bus,
        )

        self._bus_export = _bus_export = self.create_solph_node(
            label="grid_export",
            node_type=Bus,
        )

        in_levels = heat_carrier.get_levels_between(
            self.minimum_working_temperature, self.maximum_working_temperature
        )
        out_levels = heat_carrier.get_levels_between(
            in_levels[1], self.maximum_working_temperature
        )

        for temp_in, temp_out in zip(in_levels, out_levels):
            bus_warm, bus_cold, ratio = (
                heat_carrier.get_connection_heat_transfer(temp_out, temp_in)
            )
            self.create_solph_node(
                label=f"import_{temp_out:.0f}_{temp_in:.0f}",
                node_type=Converter,
                inputs={
                    bus_cold: Flow(),
                    _bus_source: Flow(),
                },
                outputs={
                    bus_warm: Flow(),
                },
                conversion_factors={
                    bus_warm: 1,
                    bus_cold: ratio,
                    _bus_source: 1 - ratio,
                },
            )

        for temp_in, temp_out in zip(in_levels, out_levels):
            bus_warm, bus_cold, ratio = (
                heat_carrier.get_connection_heat_transfer(temp_out, temp_in)
            )
            self.create_solph_node(
                label=f"export_{temp_out:.0f}_{temp_in:.0f}",
                node_type=Converter,
                inputs={
                    bus_warm: Flow(),
                },
                outputs={
                    bus_cold: Flow(),
                    _bus_export: Flow(),
                },
                conversion_factors={
                    bus_warm: 1,
                    bus_cold: ratio,
                    _bus_export: 1 - ratio,
                },
            )

        if self.working_rate is not None:
            self.create_solph_node(
                label="source_import",
                node_type=Source,
                outputs={
                    self._bus_source: Flow(
                        variable_costs=self._solph_model.data.get_timeseries(
                            self.working_rate, kind=TimeseriesType.INTERVAL
                        ),
                    )
                },
            )

    def connect(
        self,
        other: HeatGridConnection,
    ):
        self._bus_export.outputs[other._bus_source] = Flow()
        # if self.maximum_temperature < other.maximum_temperature:
        #     raise ValueError(
        #         "Maximum temperature level of the exporting HeatGridConnection must be "
        #         "higher than or equal to importing GasGridConnection at another location"
        #         "(destination). Alternative is to use heat rise to raise the temperature"
        #         " level, which is not yet implemented."
        #     )
