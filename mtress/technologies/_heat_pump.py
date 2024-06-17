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
from ..carriers import Electricity, HeatCarrier
from ..physics import calc_cop, celsius_to_kelvin
from ._abstract_technology import AbstractAnergySource, AbstractTechnology


class HeatPump(AbstractTechnology, AbstractSolphRepresentation):
    """
    Clustered heat pump for modeling power flows with variable temperature levels.

    Connects any input to any output using Converter
    with shared resources, see https://arxiv.org/abs/2012.12664

    Flows:
    E --> HP1,         E --> HP2,       E --> HP3
    A --> HP1,         A --> HP2,       A --> HP3
    1HP --> HP1,     1HP --> HP2,     1HP --> HP3
    HP0 --> Qin(T1), HP1 --> Qin(T2), HP2 --> Qin(T3)

    Sketch:
        Resources     | Technologies |  Layer Inputs

               ┏━━━━━━━━━━━━━━┓
         ┌─────╂───────→[HP3]─╂────────→(Qin(T3))
         │     ┃  ┌─────↗     ┃            ↓
       (E,A)───╂──┼────→[HP2]─╂────────→(Qin(T2))
         │     ┃  │┌─────↗    ┃            ↓
         └─────╂──┼┼───→[HP1]─╂────────→(Qin(T1))
               ┃ [1HP]────↗   ┃
               ┗━━━━━━━━━━━━━━┛

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
        max_temp_secondary: float = None,
        min_temp_secondary: float = None,
    ):
        """
        # Initialize heat pump component.

        # :param thermal_power_limit: Thermal power limit on all temperature ranges
        # :param cop_0_35: COP for the temperature rise 0°C to 35°C
        # :param anergy_sources: Anergy sources (names) to connect to, defaults to all
        # :param max_temp_primary: This is a float
        """
        super().__init__(name=name)

        self.electrical_power_limit = electrical_power_limit
        self.thermal_power_limit = thermal_power_limit
        self.cop_0_35 = cop_0_35
        self.max_temp_primary = max_temp_primary
        self.min_temp_primary = min_temp_primary
        self.max_temp_secondary = max_temp_secondary
        self.min_temp_secondary = min_temp_secondary

        # Solph specific parameters
        self.electricity_bus = None
        self.heat_budget_bus = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        # Add electrical connection
        electricity_carrier = self.location.get_carrier(Electricity)

        self.electricity_bus = self.create_solph_node(
            label="electricity",
            node_type=Bus,
            inputs={electricity_carrier.distribution: Flow(nominal_value=self.electrical_power_limit)},
        )

        # Create bus and source for a combined thermal power limit on all temperature
        # levels
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

        heat_bus_warm_primary, heat_bus_cold_primary, ratio_primary = (
            heat_carrier.get_connection_heat_transfer(
                self.max_temp_primary,
                self.min_temp_primary,
            )
        )

        heat_bus_warm_secondary, heat_bus_cold_secondary, ratio_secondary = (
            heat_carrier.get_connection_heat_transfer(
                self.max_temp_secondary, self.min_temp_secondary
            )
        )


        # for lower_temperature, hight_temperature in zip(
        #             heat_carrier.level_nodes, heat_carrier.level_nodes[1:]
        #         ):
        cop = calc_cop(
            temp_primary_in=celsius_to_kelvin(self.max_temp_primary),
            temp_primary_out=celsius_to_kelvin(self.min_temp_primary),
            temp_secondary_in=celsius_to_kelvin(self.max_temp_secondary),
            temp_secondary_out=celsius_to_kelvin(self.min_temp_secondary),
            cop_0_35=self.cop_0_35,
        )

        self.create_solph_node(
            label=f"{self.max_temp_primary}_{self.max_temp_secondary:.0f}",
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
                heat_bus_warm_primary: (cop-1)/cop/(1-ratio_primary),
                heat_bus_cold_secondary: ratio_secondary/(1-ratio_secondary),
                self.electricity_bus: 1/cop,
                self.heat_budget_bus: 1,
                heat_bus_cold_primary: (cop-1)/cop*ratio_primary/(1-ratio_primary),
                heat_bus_warm_secondary: 1/(1-ratio_secondary),
            },
        )
