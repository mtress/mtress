"""
Heat pump to be used with the layered heat energy carrier.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""

from typing import Optional

from oemof.solph import Bus, Flow
from oemof.solph.components import Source, Converter

from .._abstract_component import AbstractSolphRepresentation
from ..carriers import ElectricityCarrier, HeatCarrier
from ..physics import calc_cop, celsius_to_kelvin
from ._abstract_technology import AbstractAnergySource, AbstractTechnology


class HeatPump(AbstractTechnology, AbstractSolphRepresentation):
    """
    Clustered heat pump for modeling power flows with variable temperature levels.

    Connects any input to any output using Converter
    with shared resources, see https://arxiv.org/abs/2012.12664

    The heat pump is modelled as an array of virtual heat pumps,
    each with the correct COP for the corresponding temperatures.
    To not allow producing more heat than the real heat pump,
    all these virtual heat pumps share anergy and energy sources
    and can further have one shared virtual normalisation source (1HP).

    The heat pump also connects to every available anergy source at
    the location. The COPs are automatically calculated based on the
    information given by the heat carrier and the anergy sources.
    """

    def __init__(
        self,
        name: str,
        electrical_power_limit: float = None,
        thermal_power_limit: float = None,
        cop_0_35: float = 4.6,
        max_temp_primary: float = None,
        min_temp_primary: float = None,
        min_delta_temp_primary: float = 5.0,
        max_temp_secondary: float = None,
        min_temp_secondary: float = None,
        min_delta_temp_secondary: float = 5.0,
    ):
        """
        Initialize heat pump component.

        :param thermal_power_limit: Thermal power limit on all temperature ranges
        :param cop_0_35: COP for the temperature rise 0°C to 35°C
        :param max_temp_primary: Maximum inlet temperature (°C) at the cold side.
        :param min_temp_primary: Minimum outlet temperature (°C) at the cold side.
        :param min_delta_temp_primary: Minumum delta (°C) at the cold side.
        :param max_temp_secondary: Maximum outlet temperature (°C) at the warm side.
        :param min_temp_secondary: Minimum inlet temperature (°C) at the warm side.
        :param min_delta_temp_secondary: Minumum delta (°C) at the warm side.
        """
        super().__init__(name=name)

        self.electrical_power_limit = electrical_power_limit
        self.thermal_power_limit = thermal_power_limit
        self.cop_0_35 = cop_0_35
        self.max_temp_primary = max_temp_primary
        self.min_temp_primary = min_temp_primary
        self.min_delta_temp_primary = min_delta_temp_primary
        self.max_temp_secondary = max_temp_secondary
        self.min_temp_secondary = min_temp_secondary
        self.min_delta_temp_secondary = min_delta_temp_secondary

        # Solph specific parameters
        self.electricity_bus = None
        self.heat_budget_bus = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        # Add electrical connection
        electricity_carrier = self.location.get_carrier(ElectricityCarrier)

        self.electricity_bus = self.create_solph_node(
            label="electricity",
            node_type=Bus,
            inputs={
                electricity_carrier.distribution: Flow(
                    nominal_value=self.electrical_power_limit
                )
            },
        )

        self.heat_budget_bus = heat_budget_bus = self.create_solph_node(
            label="heat_budget",
            node_type=Bus,
        )

        self.create_solph_node(
            label="heat_budget_source",
            node_type=Source,
            outputs={heat_budget_bus: Flow(nominal_value=self.thermal_power_limit)},
        )

    def establish_interconnections(self):
        """Add connections to anergy sources."""
        heat_carrier = self.location.get_carrier(HeatCarrier)

        primary_out_levels = heat_carrier.get_levels_between(
            self.min_temp_primary, self.max_temp_primary - self.min_delta_temp_primary
        )
        primary_in_levels = heat_carrier.get_levels_between(
            primary_out_levels[0] + self.min_delta_temp_primary, self.max_temp_primary
        )

        secondary_in_levels = heat_carrier.get_levels_between(
            self.min_temp_secondary,
            self.max_temp_secondary - self.min_delta_temp_secondary,
        )
        secondary_out_levels = heat_carrier.get_levels_between(
            secondary_in_levels[0] + self.min_delta_temp_secondary,
            self.max_temp_secondary,
        )

        temp_primary_out = primary_out_levels[0]
        temp_primary_in = primary_in_levels[0]
        temp_secondary_in = secondary_in_levels[0]
        temp_secondary_out = secondary_out_levels[0]

        for (
            temp_primary_out,
            temp_primary_in,
        ) in zip(
            primary_out_levels,
            primary_in_levels,
        ):
            for (
                temp_secondary_in,
                temp_secondary_out,
            ) in zip(
                secondary_in_levels,
                secondary_out_levels,
            ):
                self._create_converter_node(
                    temp_primary_out,
                    temp_primary_in,
                    temp_secondary_in,
                    temp_secondary_out,
                )

    def _create_converter_node(
        self, temp_primary_out, temp_primary_in, temp_secondary_in, temp_secondary_out
    ):
        heat_carrier = self.location.get_carrier(HeatCarrier)
        (
            heat_bus_warm_primary,
            heat_bus_cold_primary,
            ratio_primary,
        ) = heat_carrier.get_connection_heat_transfer(temp_primary_in, temp_primary_out)

        (
            heat_bus_warm_secondary,
            heat_bus_cold_secondary,
            ratio_secondary,
        ) = heat_carrier.get_connection_heat_transfer(
            temp_secondary_out, temp_secondary_in
        )
        cop = calc_cop(
            temp_primary_in=celsius_to_kelvin(temp_primary_in),
            temp_primary_out=celsius_to_kelvin(temp_primary_out),
            temp_secondary_in=celsius_to_kelvin(temp_secondary_in),
            temp_secondary_out=celsius_to_kelvin(temp_secondary_out),
            cop_0_35=self.cop_0_35,
        )

        self.create_solph_node(
            label=f"cop_{temp_primary_in:.0f}_{temp_secondary_out:.0f}",
            node_type=Converter,
            inputs={
                heat_bus_warm_primary: Flow(),
                heat_bus_cold_secondary: Flow(),
                self.electricity_bus: Flow(),
                self.heat_budget_bus: Flow(),
            },
            outputs={
                heat_bus_cold_primary: Flow(),
                heat_bus_warm_secondary: Flow(),
            },
            conversion_factors={
                heat_bus_warm_primary: (cop - 1) / cop / (1 - ratio_primary),
                heat_bus_cold_secondary: ratio_secondary / (1 - ratio_secondary),
                self.electricity_bus: 1 / cop,
                self.heat_budget_bus: 1,
                heat_bus_cold_primary: (cop - 1)
                / cop
                * ratio_primary
                / (1 - ratio_primary),
                heat_bus_warm_secondary: 1 / (1 - ratio_secondary),
            },
        )
