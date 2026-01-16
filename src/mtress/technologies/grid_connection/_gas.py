from __future__ import annotations

import logging
from typing import Optional

from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Sink, Source

from mtress.carriers import GasCarrier
from mtress.physics import Gas

from ._abstract_grid_connection import AbstractGridConnection

from ..._constants import EnergyType

LOGGER = logging.getLogger(__file__)


class GasGridConnection(AbstractGridConnection):
    """
    The gas grid connection represents the distribution pipelines for
    a specific gas type, identified by the `gas_type` parameter. It
    allows gas import at a specific pressure level, making it essential
    to provide the `grid_pressure` parameter for connecting to the
    GasCarrier bus associated with the specified gas type at the given
    pressure level.

    Note: Working_rate must be defined to enable gas import for your
          energy system.
          Revenue must be defined to enable the gas export to gas grid
          connection of the same location.
    """

    def __init__(
        self,
        *,
        gas_type: Gas,
        grid_pressure: float,
        working_rate: Optional[float] = None,
        demand_rate: Optional[float] = 0,
        revenue: Optional[float] = None,
        **kwargs,
    ):
        """
        :gas_type: import a gas constant e.g. HYDROGEN
        :grid_pressure: in bar
        :working_rate: in currency/Wh
        :demand_rate: in currency/Wh
        :revenue: in currency/Wh
        """

        super().__init__()
        self.gas_type = gas_type
        self.grid_pressure = grid_pressure
        self.working_rate = working_rate
        self.demand_rate = demand_rate
        self.revenue = revenue

        self.b_grid_import = None
        self.b_grid_export = None

    def build_core(self):
        super().build_core()

        gas_carrier = self.location.get_carrier(GasCarrier)

        pressure_level_low, pressure_level_high = (
            gas_carrier.get_surrounding_levels(
                self.gas_type, self.grid_pressure
            )
        )

        self.b_grid_export = self.create_solph_node(
            label="grid_export",
            node_type=Bus,
            inputs={
                gas_carrier.inputs[self.gas_type][pressure_level_high]: Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.GAS,
                    }
                )
            },
        )

        self.b_grid_import = self.create_solph_node(
            label="grid_import",
            node_type=Bus,
            outputs={
                gas_carrier.inputs[self.gas_type][pressure_level_low]: Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.GAS,
                    }
                )
            },
        )

        if self.working_rate is not None:
            if self.demand_rate:
                maximum_load = Investment(ep_costs=self.demand_rate)
            else:
                maximum_load = None

            self.create_solph_node(
                label="source_import",
                node_type=Source,
                outputs={
                    self.b_grid_import: Flow(
                        nominal_value=maximum_load,
                        variable_costs=self.working_rate,
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.GAS,
                        },
                    )
                },
            )

        if self.revenue is not None:
            self.create_solph_node(
                label="sink_export",
                node_type=Sink,
                inputs={
                    self.b_grid_export: Flow(
                        variable_costs=-self.revenue,
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.GAS,
                        },
                    )
                },
            )

    def connect(
        self,
        other: GasGridConnection,
    ):
        # TODO create the actual flows between the location
        # in establish interconnections
        self.b_grid_export.outputs[other.b_grid_import] = Flow(
            custom_properties={
                "unit": "kg/h",
                "energy_type": EnergyType.GAS,
            }
        )
        if self.grid_pressure < other.grid_pressure:
            raise ValueError(
                """
                Pressure level of the exporting GasGridConnection should 
                be higher than or equal to importing GasGridConnection at 
                another location (destination). Alternative is to use
                compressor to raise the pressure level, which is not yet 
                implemented.
                """
            )
