# -*- coding: utf-8 -*-

"""
basic heat layer functionality

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Sunke Schlüters


SPDX-License-Identifier: MIT
"""

from oemof.solph import Bus, Flow
from oemof.solph.components import Source

from .._abstract_component import AbstractSolphRepresentation
from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ..carriers import ElectricityCarrier
from ._abstract_technology import AbstractTechnology


class RenewableElectricitySource(AbstractTechnology, AbstractSolphRepresentation):
    """A generic electricity source."""

    def __init__(
        self,
        name: str,
        nominal_power: float,
        specific_generation: TimeseriesSpecifier,
        fixed: bool = True,
    ):
        """
        Initialize generic electricity source.

        :param nominal_power: Nominal power of the source (in W).
        :param specific_generation: Timeseries of generated power (values in [0,1]).
        :param fixed: Indicate if the generation is fixed to the values defined by
            nominal_power and specific_generation or bounded by these values.
        """
        super().__init__(name=name)

        self.nominal_power = nominal_power
        self.specific_generation = specific_generation

        self.fixed = fixed

    def build_core(self):
        """Build oemof solph core structure."""
        electricity_carrier = self.location.get_carrier(ElectricityCarrier)

        if self.fixed:
            flow = Flow(
                nominal_value=self.nominal_power,
                fix=self._solph_model.data.get_timeseries(
                    self.specific_generation, kind=TimeseriesType.INTERVAL
                ),
            )
        else:
            flow = Flow(
                nominal_value=self.nominal_power,
                max=self._solph_model.data.get_timeseries(
                    self.specific_generation, kind=TimeseriesType.INTERVAL
                ),
            )

        local_bus = self.create_solph_node(
            label="connection",
            node_type=Bus,
            outputs={
                electricity_carrier.feed_in: Flow(),
                electricity_carrier.distribution: Flow(),
            },
        )

        self.create_solph_node(
            label="source",
            node_type=Source,
            outputs={local_bus: flow},
        )
