"""Electricity grid connection."""

from typing import Optional

from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Sink, Source

from mtress._data_handler import TimeseriesSpecifier, TimeseriesType
from mtress.carriers import ElectricityCarrier

from ..._energy_types import EnergyType
from ._abstract_grid_connection import AbstractGridConnection


class ElectricityGridConnection(AbstractGridConnection):

    def __init__(
        self,
        label,
        *,
        working_rate: Optional[TimeseriesSpecifier] = None,
        revenue: Optional[TimeseriesSpecifier] = None,
        demand_rate: Optional[float] = 0,
        grid_import_limit: Optional[float] = None,
        grid_export_limit: Optional[float] = None,
        parent_node=None,
        custom_properties=None,
    ) -> None:
        """
        :working_rate: in currency/Wh
        :revenue: in currency/Wh
        :demand_rate: in currency/Wh
        :grid_import_limit: limits the grid's imports (in W)
        """
        super().__init__(
            label=label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        self.working_rate = working_rate
        self.demand_rate = demand_rate
        self.revenue = revenue
        self.grid_import_limit = grid_import_limit
        self.grid_export_limit = grid_export_limit

        self.grid_export = None
        self.grid_import = None

        self._build_core()

    def _build_core(self):

        self.grid_import = b_grid_import = self.subnode(
            Bus,
            local_name="grid_import",
        )

        self.grid_export = b_grid_export = self.subnode(
            Bus,
            local_name="grid_export",
        )

        self.inbound_interfaces[ElectricityCarrier] = [
            self.grid_import,
            self.grid_export,
        ]
        self.outbound_interfaces[ElectricityCarrier] = [
            self.grid_import,
            self.grid_export,
        ]

        if self.revenue is not None:
            self.subnode(
                Sink,
                local_name="sink_export",
                inputs={
                    b_grid_export: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.ELECTRICITY,
                        },
                        nominal_capacity=self.grid_export_limit,
                        variable_costs=-self._energy_system.data.get_timeseries(
                            self.revenue, kind=TimeseriesType.INTERVAL
                        ),
                    )
                },
            )

        if self.working_rate is not None:
            if self.demand_rate:
                maximum_load = Investment(
                    ep_costs=self.demand_rate, maximum=self.grid_import_limit
                )
            else:
                maximum_load = self.grid_import_limit

            self.subnode(
                Source,
                local_name="source_import",
                outputs={
                    b_grid_import: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.ELECTRICITY,
                        },
                        nominal_capacity=maximum_load,
                        variable_costs=self._energy_system.data.get_timeseries(
                            self.working_rate, kind=TimeseriesType.INTERVAL
                        ),
                    )
                },
            )

    def establish_interconnections(self):
        if self.parent:
            electricity_carrier = self.parent.get_carrier(ElectricityCarrier)

            self.grid_export.inputs[electricity_carrier.feed_in] = Flow(
                custom_properties={
                    "unit": "W",
                    "energy_type": EnergyType.ELECTRICITY,
                }
            )

            self.grid_import.outputs[electricity_carrier.distribution] = Flow(
                custom_properties={
                    "unit": "W",
                    "energy_type": EnergyType.ELECTRICITY,
                }
            )

    def _connect(
        self,
        other: ElectricityGridConnection,
    ):
        self.grid_export.outputs[other.grid_import] = Flow(
            custom_properties={
                "unit": "W",
                "energy_type": EnergyType.ELECTRICITY,
            }
        )
