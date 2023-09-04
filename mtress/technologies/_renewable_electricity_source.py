# -*- coding: utf-8 -*-

"""
basic heat layer functionality

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Sunke Schlüters


SPDX-License-Identifier: MIT
"""

from oemof.solph import Flow
from oemof.solph.components import Source

from .._abstract_component import AbstractSolphRepresentation
from .._data_handler import TimeseriesSpecifier
from ..carriers import Electricity
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

        :param nominal_power: Nominal power of the source.
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
        electricity_carrier = self.location.get_carrier(Electricity)

        flow = (
            Flow(nominal_value=self.nominal_power, fix=self.specific_generation)
            if self.fixed
            else Flow(nominal_value=self.nominal_power, max=self.specific_generation)
        )

        self.create_solph_node(
            label="source",
            node_type=Source,
            outputs={electricity_carrier.production: flow},
        )
