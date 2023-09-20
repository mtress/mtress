# -*- coding: utf-8 -*-

"""Basic hydrogen functionality."""

from oemof.solph import Bus, Flow

from .._abstract_component import AbstractSolphRepresentation
from ._abstract_carrier import AbstractLayeredCarrier


class Hydrogen(AbstractLayeredCarrier, AbstractSolphRepresentation):
    """
    Connector class for modelling hydrogen flows with variable pressure levels.

    All hydrogen flows are given in kg.

    Functionality: This class represents a local gas grid with variable pressure
        levels. The concept of the energy carrier heat is expanded to
        (compressible) gas. It can be expanded from high pressure to lower
        pressure or compressed (using a compressor). The pressure level plays
        a role, especially when energy is stored in gaseous form.

        Other components and demands might be added to the energy_system by
        their respective classes / functions and are automatically connected
        to their fitting busses by the carrier.

    Procedure: Create a simple hydrogen carrier by doing the following:

            house_1.add_carrier(
                carriers.Hydrogen(levels=[250, 700])

    Notice: As hydrogen was recently implemented into MTRESS in the form of an
        electrolyzer and a hydrogen compressor, the gas carrier currently
        finds application in that field.
    """

    def __init__(self, pressure_levels: list):
        """
        Initialize hydrogen energy carrier and add components.

        :param pressure_levels: Pressure levels
        """
        super().__init__(levels=pressure_levels)

        # Init solph interfaces
        self.busses = {}

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        pressure_low = None
        for pressure in self._levels:
            if pressure_low is None:
                bus = self.create_solph_node(
                    label=f"out_{pressure:.0f}",
                    node_type=Bus,
                )
            else:
                bus = self.create_solph_node(
                    label=f"out_{pressure:.0f}",
                    node_type=Bus,
                    outputs={self.busses[pressure_low]: Flow()},
                )

            self.busses[pressure] = bus

            # prepare for next iteration of the loop
            pressure_low = pressure

    @property
    def inputs(self):
        """Alias for busses."""
        return self.busses

    @property
    def outputs(self):
        """Alias for busses."""
        return self.busses

    @property
    def pressure_levels(self):
        """Alias for levels."""
        return self.levels