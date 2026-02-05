"""Electricity energy carrier."""

from oemof.solph import Bus

from .._constants import EnergyType
from ._abstract_carrier import AbstractCarrier


class ElectricityCarrier(AbstractCarrier):
    """
    Electricity energy carrier.

    Functionality: Electricity connections at a location. This class
        represents a local electricity grid with or without connection
        to the global electricity grid.

        All default busses, sources and sinks are automatically generated
        and interconnected when the carrier is initialized. Automatically
        generated are the following: one bus each for production, distribution,
        export, grid_in (actual grid supply with costs), grid_out (external
        market to sell electricity to) as well as a source (additional
        unidirictional grid connection) and a sink (export).

        Other components and demands might be added to the energy_system by
        their respective classes / functions and are automatically connected
        to their fitting busses by the carrier.

    Procedure: Create a simple electricity carrier by doing the following
        and adding costs to the grid supply.

    """

    def __init__(
        self,
        *,
        parent_node=None,
        custom_properties=None,
    ):
        """Initialize electricity carrier."""
        super().__init__(
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        self._build_core()

    def _build_core(self):
        self.distribution = self.subnode(
            Bus,
            local_name="distribution",
        )
        self.feed_in = self.subnode(
            Bus,
            local_name="feed_in",
        )

        self.inbound_interfaces[EnergyType.ELECTRICITY] = self.subnodes
        self.outbound_interfaces[EnergyType.ELECTRICITY] = self.subnodes

    def establish_interconnections(self):
        pass
