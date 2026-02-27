# -*- coding: utf-8 -*-

"""
Renewable energy source

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Sunke Schlüters


SPDX-License-Identifier: MIT
"""

from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Source

from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ..carriers import ElectricityCarrier
from ._abstract_technology import AbstractTechnology

from .._constants import EnergyType


class RenewableElectricitySource(AbstractTechnology):
    """A generic renewable electricity source."""

    def __init__(
        self,
        name: str,
        nominal_power: Investment | float,
        specific_generation: TimeseriesSpecifier,
        working_rate: TimeseriesSpecifier = 0,
        fixed: bool = True,
    ):
        """
        Initialize generic electricity source.

        :param nominal_power: Nominal power of the source (in W).
        :param specific_generation: Timeseries of generated power
            (values in [0,1]).
        :param working rate: Timeseries or fixed cost (in EUR/Wh),
            defaults to 0
        :param fixed: Indicate if the generation is fixed to the values
            defined by nominal_power and specific_generation or bounded
            by these values.
        """
        super().__init__(name=name)

        self.nominal_power = nominal_power
        self.specific_generation = specific_generation
        self.working_rate = working_rate
        self.fixed = fixed

    def build_core(self):
        """Build oemof solph core structure."""
        super().build_core()

        electricity_carrier = self.location.get_carrier(ElectricityCarrier)

        if self.fixed:
            flow = Flow(
                custom_properties={
                    "unit": "W",
                    "energy_type": EnergyType.ELECTRICITY,
                },
                nominal_value=self.nominal_power,
                variable_costs=self._solph_model.data.get_timeseries(
                    self.working_rate, kind=TimeseriesType.INTERVAL
                ),
                fix=self._solph_model.data.get_timeseries(
                    self.specific_generation, kind=TimeseriesType.INTERVAL
                ),
            )
        else:
            flow = Flow(
                custom_properties={
                    "unit": "W",
                    "energy_type": EnergyType.ELECTRICITY,
                },
                nominal_value=self.nominal_power,
                variable_costs=self._solph_model.data.get_timeseries(
                    self.working_rate, kind=TimeseriesType.INTERVAL
                ),
                max=self._solph_model.data.get_timeseries(
                    self.specific_generation, kind=TimeseriesType.INTERVAL
                ),
            )

        local_bus = self.create_solph_node(
            label="connection",
            node_type=Bus,
            outputs={
                electricity_carrier.feed_in: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    }
                ),
                electricity_carrier.distribution: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    }
                ),
            },
        )

        self.create_solph_node(
            label="source",
            node_type=Source,
            outputs={local_bus: flow},
        )
