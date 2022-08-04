# -*- coding: utf-8 -*-

"""Basic hydrogen functionality."""

from oemof import solph

from ._abstract_carrier import AbstractLayeredCarrier


class Hydrogen(AbstractLayeredCarrier):
    """
    Connector class for modelling hydrogen flows with variable pressure levels.

    All hydrogen flows are given in kg.
    """

    def __init__(self, pressure_levels: list, **kwargs):
        """
        Initialize hydrogen energy carrier and add components.

        :param pressure_levels: Pressure levels
        """
        super().__init__(levels=pressure_levels, **kwargs)

        self.outputs = {}

        pressure_low = None
        for pressure in self._levels:
            bus_label = self._generate_label(f"out_{pressure:.0f}")

            if pressure_low is None:
                bus = solph.Bus(label=bus_label)
            else:
                bus = solph.Bus(
                    label=bus_label,
                    outputs={self.outputs[pressure_low]: solph.Flow()},
                )

            self.outputs[pressure] = bus
            self.location.energy_system.add(bus)

            # prepare for next iteration of the loop
            pressure_low = pressure

    @property
    def inputs(self):
        """Alias for outputs."""
        return self.outputs
