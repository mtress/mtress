# -*- coding: utf-8 -*-

"""Basic hydrogen functionality."""

from oemof import solph

from .._abstract_component import AbstractSolphComponent
from ._abstract_carrier import AbstractLayeredCarrier


class Hydrogen(AbstractLayeredCarrier, AbstractSolphComponent):
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

        # Init solph interfaces
        self.busses = {}

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        pressure_low = None
        for pressure in self._levels:
            if pressure_low is None:
                bus = self._solph_model.add_solph_component(
                    mtress_component=self,
                    label=f"out_{pressure:.0f}",
                    solph_component=solph.Bus,
                )
            else:
                bus = self._solph_model.add_solph_component(
                    mtress_component=self,
                    label=f"out_{pressure:.0f}",
                    solph_component=solph.Bus,
                    outputs={self.busses[pressure_low]: solph.Flow()},
                )

            self.busses[pressure] = bus

            # prepare for next iteration of the loop
            pressure_low = pressure

    @property
    def inputs(self):
        """Alias for outputs."""
        return self.busses

    @property
    def pressure_levels(self):
        """Alias for levels."""
        return self.levels
