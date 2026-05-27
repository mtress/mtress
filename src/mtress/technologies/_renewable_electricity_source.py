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

from .._constants import EnergyType
from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ..carriers import ElectricityCarrier
from .._base_mtress_nodes import AbstractTechnology


class RenewableElectricitySource(AbstractTechnology):
    """A generic renewable electricity source."""

    def __init__(
        self,
        label,
        *,
        nominal_power: Investment | float,
        specific_generation: TimeseriesSpecifier,
        working_rate: TimeseriesSpecifier = 0,
        fixed: bool = True,
        location=None,
        custom_properties=None,
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
        super().__init__(
            label,
            location=location,
            custom_properties=custom_properties,
        )

        self._nominal_power = nominal_power
        self._specific_generation = specific_generation
        self._working_rate = working_rate
        self._fixed = fixed

        self._build_core()

    def _build_core(self):
        # TODO!
        self._output_node = self.subnode(
            Bus,
            local_name="output",
        )

        if self._fixed:
            flow = Flow(
                custom_properties={
                    "unit": "W",
                    "energy_type": EnergyType.ELECTRICITY,
                },
                nominal_capacity=self._nominal_power,
                variable_costs=self._working_rate,
                fix=self._specific_generation,
            )
        else:
            flow = Flow(
                custom_properties={
                    "unit": "W",
                    "energy_type": EnergyType.ELECTRICITY,
                },
                nominal_capacity=self._nominal_power,
                variable_costs=self._working_rate,
                max=self._specific_generation,
            )

        self.subnode(
            Source,
            local_name="source",
            outputs={self._output_node: flow},
        )
        self.outbound_interfaces[EnergyType.ELECTRICITY] = [self._output_node]

    def establish_interconnections(self):
        if self.parent:
            electricity_carrier = self.parent.get_carrier(ElectricityCarrier)

            self._output_node.outputs[electricity_carrier.distribution] = Flow(
                custom_properties={
                    "unit": "W",
                    "energy_type": EnergyType.ELECTRICITY,
                }
            )
            self._output_node.outputs[electricity_carrier.feed_in] = Flow(
                custom_properties={
                    "unit": "W",
                    "energy_type": EnergyType.ELECTRICITY,
                }
            )
