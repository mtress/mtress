"""This module provide gas carrier in MTRESS"""

from oemof.solph import Bus, Flow

from .._abstract_component import AbstractSolphRepresentation
from ._abstract_carrier import AbstractLayeredCarrier


class Gas(AbstractLayeredCarrier, AbstractSolphRepresentation):
    """
    Gas energy carrier.

    Functionality: Gas connections at a location. This class
        represents a local gas grid with or without connection
        to the global gas grid.

        All gas flows in MTRESS except H2 are given in KWh. Therefore, the
        calorific values should also be based on KWh.

        All default busses, are automatically generated and interconnected when
        the carrier is initialized. Automatically generated are the following:
        one bus each for feed_in and distribution at each specific pressure level.
        Feed_in takes place at grid pressure level and grid import is connected to
        distribution bus based on the grid pressure level.

        Other components and demands might be added to the energy_system by
        their respective classes / functions and are automatically connected
        to their fitting busses by the carrier.

    """

    def __init__(
            self,
            pressure_levels: list,
            feed_in_pressure: float
    ):
        """
        Initialize natural gas carrier.

        :param pressure_levels: List of pressure levels for the chosen gas carrier
        :param feed_in_pressure: Pressure level at which gas should be exported to
                                 grid.
        """

        super().__init__(levels=pressure_levels)

        # Properties for connection oemof.solph busses
        self.feed_in_pressure = feed_in_pressure
        self.distribution = {}
        self.feed_in = {}

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        pressure_low = None
        for pressure in self._levels:
            if pressure_low is None:
                bus = self.create_solph_node(
                    label=f"dist_out_{pressure:.0f}",
                    node_type=Bus,
                )
            else:
                bus = self.create_solph_node(
                    label=f"dist_out_{pressure:.0f}",
                    node_type=Bus,
                    outputs={self.distribution[pressure_low]: Flow()},
                )

            self.distribution[pressure] = bus

            # prepare for next iteration of the loop
            pressure_low = pressure

        if self.feed_in_pressure in self._levels:
            feed_bus = self.create_solph_node(
                       label=f"feed_in_{self.feed_in_pressure:.0f}",
                       node_type=Bus,
                       outputs={}
            )

            self.feed_in[self.feed_in_pressure] = feed_bus

    @property
    def inputs(self):
        """Alias for busses."""
        return self.distribution

    @property
    def outputs(self):
        """Alias for busses."""
        return self.distribution

    @property
    def pressure_levels(self):
        """Alias for levels."""
        return self.levels
