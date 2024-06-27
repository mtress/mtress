"""Electricity energy carrier."""

from oemof.solph import Bus

from .._abstract_component import AbstractSolphRepresentation
from ._abstract_carrier import AbstractCarrier


class ElectricityCarrier(AbstractCarrier, AbstractSolphRepresentation):
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
    ):
        """Initialize electricity carrier."""
        super().__init__()

        # Properties for connection oemof.solph busses
        self.distribution = None
        self.feed_in = None

    def build_core(self):
        self.distribution = self.create_solph_node(
            label="distribution",
            node_type=Bus,
        )

        self.feed_in = self.create_solph_node(
            label="feed_in",
            node_type=Bus,
        )
