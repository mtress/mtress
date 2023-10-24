# -*- coding: utf-8 -*-

"""
Basic heat layer functionality.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""

from oemof.solph import Bus, Flow
from oemof.solph.components import Converter

from .._abstract_component import AbstractSolphRepresentation
from ._abstract_carrier import AbstractLayeredCarrier


class Heat(AbstractLayeredCarrier, AbstractSolphRepresentation):
    """
    Connector class for modelling power flows with variable temperature levels.

    This class models a heat bus system with configurable temperature levels
    (see https://arxiv.org/abs/2012.12664). The temperature levels can
    represent flow and return of a room heating system or various tapping
    temperatures.

      Layer Inputs        Layers Outputs

      (Qin(T3))           (Q(T3))
          │   ↘           ↗
          │    [rise 2, 3]
          ↓               ↖
      (Qin(T2))           (Q(T2))
          │    ↘          ↗
          │    [rise 1, 2]
          ↓               ↖
      (Qin(T1))---------->(Q(T1))
          ↓
      (Qin(T-1))--------->(Q(T-1))
              ↘          ↗   │
               [rise-2,-1]   │
                         ↖   ↓
                          (Q(T-2))


    Heat sources connect to the Qin for the corresponding temperatures.
    If efficiency increases with lower temperature,
    techs should connect to all input nodes (see e.g. HeatPump).
    Note that there are also heat supply techs with constant efficiency.
    Those only need to connect to the hottest layer.

    Functionality: Heat connections at a location. This class represents a local heat
       grid. The energy carrier heat allows to optimise both, temperature and heat,
       as the temperature has a significant impact on the performance of renewable
       energy supply systems. This is done by defining several discrete temperature
       levels.
       Besides the temperature levels, a reference temperature can be defined.
       This can be useful to simplify the model by setting the reference
       to a return temperature, resulting in the corresponding return flow to be
       considered at zero energy.

       Other components and demands might be added to the energy_system by
       their respective classes / functions and are automatically connected
       to their fitting busses by the carrier.

    Procedure: Create a simple heat carrier by doing the following

           house_1.add(carriers.Heat(temperature_levels=[30],
                                             reference_temperature=20))
    """

    def __init__(
        self,
        temperature_levels: list[float],
        reference_temperature: float = 0,
    ):
        """
        Initialize heat energy carrier and add components.

        :param temperature_levels: Temperature levels
        :param reference_temperature: Reference temperature
        """
        if reference_temperature not in temperature_levels:
            temperature_levels = temperature_levels + [reference_temperature]
        super().__init__(
            levels=temperature_levels,
            reference=reference_temperature,
        )

        self._reference_level = self._levels.index(reference_temperature)

        # Properties for solph interfaces
        self.outputs = {}
        self.inputs = {}
 
    @property
    def reference_level(self):
        """Return index or key of reference level"""
        return self._reference_level

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        bus_in = None
        bus_out = None
        bus_in_inputs = {}

        # Thermal layers
        for temperature in reversed(self._levels):
            bus_in = self.create_solph_node(
                label=f"in_{temperature:.0f}",
                node_type=Bus,
                inputs=bus_in_inputs,
            )

            self.inputs[temperature] = bus_in
            bus_in_inputs = {bus_in: Flow()}

            bus_out = self.create_solph_node(
                label=f"out_{temperature:.0f}",
                node_type=Bus,
            )

            self.outputs[temperature] = bus_out
        
        # add direct flows for the levels close to reference
        if self.reference < self._levels[-1]:
            temperature_above_reference = self._levels[self.reference_level+1]
            self.outputs[temperature_above_reference].inputs[
                self.inputs[temperature_above_reference]
            ] = Flow()
        
        if self.reference > self._levels[0]:
            bus_out.inputs[self.reference].outputs[
                self._levels[self.reference_level-1]
            ] = Flow()

        # rise above reference temperature
        for temp_low, temp_high in zip(
            self._levels[self.reference_level+1:],
            self._levels[self.reference_level+2:]
        ):
            bus_out_high = self.outputs[temp_high]
            bus_out_low = self.outputs[temp_low]
            bus_in_high = self.inputs[temp_high]

            ratio = (temp_low - self.reference) / (temp_high - self.reference)
            
            # Temperature riser
            self.create_solph_node(
                label=f"rise_{temp_low:.0f}_{temp_high:.0f}",
                node_type=Converter,
                inputs={
                    bus_in_high: Flow(),
                    bus_out_low: Flow(),
                },
                outputs={bus_out_high: Flow()},
                conversion_factors={
                    bus_in_high: 1 - ratio,
                    bus_out_low: ratio,
                    bus_out_high: 1,
                },
            )
