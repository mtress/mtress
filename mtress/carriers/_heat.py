# -*- coding: utf-8 -*-

"""
Basic heat layer functionality.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""

from oemof import solph

from .._abstract_component import AbstractSolphComponent
from ._abstract_carrier import AbstractLayeredCarrier


class Heat(AbstractLayeredCarrier, AbstractSolphComponent):
    """
    Connector class for modelling power flows with variable temperature levels.

    This class models a heat bus system with configurable temperature levels
    (see https://arxiv.org/abs/2012.12664). The temperature levels can
    represent flow and return of a room heating system or various tapping
    temperatures.

      Layer Inputs        Layers Outputs

      (Qin(T3))           (Q(T3))
          │   ↘           ↗
          │    [heater2,3]
          ↓               ↖
      (Qin(T2))           (Q(T2))
          │    ↘          ↗
          │    [heater1,2]
          ↓               ↖
      (Qin(T1))---------->(Q(T1))

    Heat sources connect to the Qin for the corresponding temperatures.
    If efficiency increases with lower temperature,
    techs should connect to all input nodes (see e.g. HeatPump).
    Note that there are also heat supply techs with constant efficiency.
    Those only need to connect to the hottest layer.
    """

    def __init__(self, temperature_levels: list, reference_temperature=0, **kwargs):
        """
        Initialize heat energy carrier and add components.

        :param temperature_levels: Temperature levels
        :param reference_temperature: Reference temperature
        """
        super().__init__(levels=temperature_levels, **kwargs)

        # Defining temperatures
        # If no reference temperature is given, we use 0°C
        self._reference = reference_temperature

        assert self._reference < self._levels[0], (
            "Reference temperature should be lower than the lowest temperature" " level"
        )

        # Properties for solph interfaces
        self.outputs = {}
        self.inputs = {}

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        temp_low = None
        for temperature in self._levels:
            # Thermal buses
            b_out = self._solph_model.add_solph_component(
                mtress_component=self,
                label=f"out_{temperature:.0f}",
                solph_component=solph.Bus,
            )

            if temp_low is None:
                bus_in = self._solph_model.add_solph_component(
                    mtress_component=self,
                    label=f"in_{temperature:.0f}",
                    solph_component=solph.Bus,
                    outputs={b_out: solph.Flow()},
                )
            else:
                bus_in = self._solph_model.add_solph_component(
                    mtress_component=self,
                    label=f"in_{temperature:.0f}",
                    solph_component=solph.Bus,
                    outputs={
                        self.inputs[temp_low]: solph.Flow(),
                        b_out: solph.Flow(),
                    },
                )

            self.outputs[temperature] = b_out
            self.inputs[temperature] = bus_in

            # Temperature risers
            if temp_low is not None:
                ratio = (temp_low - self._reference) / (temperature - self._reference)

                self._solph_model.add_solph_component(
                    mtress_component=self,
                    label=f"rise_{temp_low:.0f}_{temperature:.0f}",
                    solph_component=solph.Transformer,
                    inputs={
                        bus_in: solph.Flow(),
                        self.outputs[temp_low]: solph.Flow(),
                    },
                    outputs={b_out: solph.Flow()},
                    conversion_factors={
                        bus_in: 1 - ratio,
                        self.outputs[temp_low]: ratio,
                        b_out: 1,
                    },
                )

            # prepare for next iteration of the loop
            temp_low = temperature

    @property
    def temperature_levels(self):
        """Return the list of temperature levels."""
        return self.levels

    @property
    def reference_temperature(self):
        """Return the reference temperature."""
        return self._reference
