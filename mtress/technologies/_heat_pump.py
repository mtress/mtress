"""
Heat pump to be used with the layered heat energy carrier.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""
from typing import Optional

from oemof import solph

from .._abstract_component import AbstractSolphComponent
from ..carriers import Electricity, Heat
from ..physics import calc_cop, celsius_to_kelvin
from ._abstract_technology import AbstractAnergySource, AbstractTechnology


class HeatPump(AbstractTechnology, AbstractSolphComponent):
    """
    Clustered heat pump for modeling power flows with variable temperature levels.

    Connects any input to any output using solph.Transformer
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
    To not allow producing more heat then the real heat pump,
    all these virtual heat pumps share anergy and energy sources
    and can further have one shared virtual normalisation source (1HP).
    """

    def __init__(
        self,
        name: str,
        thermal_power_limit: float = None,
        cop_0_35: float = 4.6,
        anergy_sources: Optional[list] = None,
    ):
        """
        Initialize heat pump component.

        :param thermal_power_limit: Thermal power limit on all temperature ranges
        :param cop_0_35: COP for the temperature rise 0°C to 35°C
        :param anergy_sources: Anergy sources (names) to connect to, defaults to all
        """
        super().__init__(name)

        self.thermal_power_limit = thermal_power_limit
        self.cop_0_35 = cop_0_35
        self.anergy_sources = anergy_sources

        # Solph specific parameters
        self.electricity_bus = None
        self.heat_budget_bus = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        # Add electrical connection
        electricity_carrier = self.location.get_carrier(Electricity)

        self.electricity_bus = self._solph_model.add_solph_component(
            mtress_component=self,
            label="electricity",
            solph_component=solph.Bus,
            inputs={electricity_carrier.distribution: solph.Flow()},
        )

        # Create bus and source for a combined thermal power limit on all temperature
        # levels
        heat_budget_source = self._solph_model.add_solph_component(
            mtress_component=self,
            label="heat_budget_source",
            solph_component=solph.Source,
        )

        self.heat_budget_bus = self._solph_model.add_solph_component(
            mtress_component=self,
            label="heat_budget_bus",
            solph_component=solph.Bus,
            inputs={
                heat_budget_source: solph.Flow(nominal_value=self.thermal_power_limit)
            },
        )

    def add_interconnections(self):
        """Add connections to anergy sources."""
        heat_carrier = self.location.get_carrier(Heat)

        for anergy_source in self.location.get_components(AbstractAnergySource):
            if self.anergy_sources is None or anergy_source.name in self.anergy_sources:
                # Add tranformers for each heat source.
                for target_temperature in heat_carrier.temperature_levels:
                    cop = calc_cop(
                        temp_input=celsius_to_kelvin(anergy_source.temperature),
                        temp_output=celsius_to_kelvin(target_temperature),
                        cop_0_35=self.cop_0_35,
                    )

                    self._solph_model.add_solph_component(
                        mtress_component=self,
                        label=f"{anergy_source.name}_{target_temperature:.0f}",
                        solph_component=solph.Transformer,
                        inputs={
                            anergy_source.bus: solph.Flow(),
                            self.electricity_bus: solph.Flow(),
                            self.heat_budget_bus: solph.Flow(),
                        },
                        outputs={
                            heat_carrier.inputs[target_temperature]: solph.Flow(),
                        },
                        conversion_factors={
                            self.heat_budget_bus: 1,
                            anergy_source.bus: (cop - 1) / cop,
                            self.electricity_bus: 1 / cop,
                            heat_carrier.inputs[target_temperature]: 1,
                        },
                    )
