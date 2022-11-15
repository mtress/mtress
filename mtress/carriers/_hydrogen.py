# -*- coding: utf-8 -*-

"""Basic hydrogen functionality."""

from oemof import solph

from ._abstract_carrier import AbstractLayeredCarrier


class Hydrogen(AbstractLayeredCarrier):
    """
    Connector class for modelling hydrogen flows with variable pressure levels.

    All hydrogen flows are given in kg.
    """

    """
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

    @property
    def pressure_levels(self):
        """Alias for levels."""
        return self.levels
