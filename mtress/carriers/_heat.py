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

    This class models is a heat bus system with configurable temperature levels
    (see https://arxiv.org/abs/2012.12664). The temperature levels can
    represent flow and return of a room heating system or various tapping
    temperatures.

    Layer Inputs        Layers Outputs

    (Qin(T3))          (Q(T3))
        │   ↘           ↗
        │   [riser 2, 3]
        ↓               ↖
    (Qin(T2))          (Q(T2))
        │   ↘           ↗
        │   [riser 2, 3]
        ↓               ↖
    (Qin(T1))--------->(Q(T1))
        ↓
    (Qin(T0))          (Q(T0))
        │   ↘
        │    ----------
        ↓               ↘
    (Qin(T-1))         (Q(T-1))
        │   ↘           ↙
        │   [riser-2,-1]
        ↓               ↘
    (Qin(T-2))         (Q(T-2))


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

        :param temperature_levels: Temperature levels (in °C)
        :param reference_temperature: Reference temperature (in °C)
        """
        if reference_temperature not in temperature_levels:
            temperature_levels = temperature_levels + [reference_temperature]
        super().__init__(
            levels=sorted(temperature_levels),
            reference=reference_temperature,
        )

        self._reference_index = self._levels.index(reference_temperature)

        # Properties for solph interfaces
        self.outputs = {}
        self.inputs = {}

    @property
    def reference_level(self):
        """Return index or key of reference level"""
        return self._reference_index

    @property
    def levels_above_reference(self):
        return self.levels[self._reference_index+1:]

    @property
    def levels_below_reference(self):
        return self.levels[:self._reference_index]

    @property
    def input_levels(self):
        """Return the list of input temperature levels."""
        return self.levels[1:]

    @property
    def output_levels(self):
        """Return the list of output temperature levels."""
        return self.levels

    def _create_temperature_riser(self, temp_low, temp_high):
            bus_in_pri = self.inputs[temp_high]
            if temp_low > self.reference:
                ratio = (temp_low - self.reference) / (temp_high - self.reference)
                bus_out = self.outputs[temp_high]
                bus_in_sec = self.outputs[temp_low]
            else:
                ratio = (temp_high - self.reference) / (temp_low - self.reference)
                bus_out = self.outputs[temp_low]
                bus_in_sec = self.outputs[temp_high]

            # Temperature riser
            self.create_solph_node(
                label=f"rise_{temp_low:.0f}_{temp_high:.0f}",
                node_type=Converter,
                inputs={
                    bus_in_pri: Flow(),
                    bus_in_sec: Flow(),
                },
                outputs={bus_out: Flow()},
                conversion_factors={
                    bus_in_pri: 1 - ratio,
                    bus_in_sec: ratio,
                    bus_out: 1,
                },
            )

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
            self.inputs[self.reference].outputs[
                self.outputs[self._levels[self.reference_level-1]]
            ] = Flow()

        # rise above reference temperature
        for temp_low, temp_high in zip(
            self._levels[self.reference_level+1:],
            self._levels[self.reference_level+2:]
        ):
            self._create_temperature_riser(temp_low, temp_high)

        # rise below reference temperature
        for temp_low, temp_high in zip(
            self._levels[0:self.reference_level],
            self._levels[1:self.reference_level]
        ):
            self._create_temperature_riser(temp_low, temp_high)