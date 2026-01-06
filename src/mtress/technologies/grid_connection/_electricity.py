"""Electricity grid connection."""

from __future__ import annotations

from typing import Optional

from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Sink, Source

from mtress._data_handler import TimeseriesSpecifier, TimeseriesType
from mtress.carriers import ElectricityCarrier

from ._abstract_grid_connection import AbstractGridConnection

from ..._constants import EnergyType


class ElectricityGridConnection(AbstractGridConnection):
    def __init__(
        self,
        working_rate: Optional[TimeseriesSpecifier] = None,
        revenue: Optional[TimeseriesSpecifier] = None,
        demand_rate: Optional[float] = 0,
        grid_import_limit: Optional[float] = None,
        grid_export_limit: Optional[float] = None,
    ) -> None:
        """
        :working_rate: in currency/Wh
        :revenue: in currency/Wh
        :demand_rate: in currency/Wh
        :grid_import_limit: limits the grid's imports (in W)
        """
        super().__init__()

        self.working_rate = working_rate
        self.demand_rate = demand_rate
        self.revenue = revenue
        self.grid_import_limit = grid_import_limit
        self.grid_export_limit = grid_export_limit

        self.grid_export = None
        self.grid_import = None

    def build_core(self):
        super().build_core()

        electricity_carrier = self.location.get_carrier(ElectricityCarrier)

        self.grid_import = b_grid_import = self.create_solph_node(
            label="grid_import",
            node_type=Bus,
            outputs={
                electricity_carrier.distribution: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    }
                )
            },
        )

        self.grid_export = b_grid_export = self.create_solph_node(
            label="grid_export",
            node_type=Bus,
            inputs={
                electricity_carrier.feed_in: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    }
                )
            },
        )
        if self.revenue is not None:
            self.create_solph_node(
                label="sink_export",
                node_type=Sink,
                inputs={
                    b_grid_export: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.ELECTRICITY,
                        },
                        nominal_value=self.grid_export_limit,
                        variable_costs=-self._solph_model.data.get_timeseries(
                            self.revenue, kind=TimeseriesType.INTERVAL
                        ),
                    )
                },
            )

        if self.working_rate is not None:
            if self.demand_rate:
                maximum_load = Investment(
                    ep_costs=self.demand_rate, max=self.grid_import_limit
                )
            else:
                maximum_load = self.grid_import_limit

            self.create_solph_node(
                label="source_import",
                node_type=Source,
                outputs={
                    b_grid_import: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.ELECTRICITY,
                        },
                        nominal_value=maximum_load,
                        variable_costs=self._solph_model.data.get_timeseries(
                            self.working_rate, kind=TimeseriesType.INTERVAL
                        ),
                    )
                },
            )

    def connect(
        self,
        other: ElectricityGridConnection,
    ):
        # TODO create the actual flows between the location in
        # establish interconnections
        self.grid_export.outputs[other.grid_import] = Flow(
            custom_properties={
                "unit": "W",
                "energy_type": EnergyType.ELECTRICITY,
            }
        )
