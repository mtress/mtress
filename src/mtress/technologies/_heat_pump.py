"""
Heat pump to be used with the layered heat energy carrier.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""

from dataclasses import dataclass

from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Converter, Source

from ..carriers import ElectricityCarrier, HeatCarrier
from ..physics import calc_cop
from ._abstract_technology import AbstractTechnology

from .._constants import EnergyType


@dataclass
class COPReference:
    """
    :param cold_side_in: Reference inlet temperature (°C) at cold side
        of the HP, e.g., evaporator.
    :param cold_side_out: Reference outlet temperature (°C) at cold side
        of the HP, e.g., evaporator.
    :param warm_side_out: Reference outlet temperature (°C) at warm side
        of the HP, e.g., condenser.
    :param warm_side_in: Reference inlet temperature (°C) at warm side
        of the HP, e.g., condenser.
    """

    cop: float = 4.6
    cold_side_in: float = 0.0
    cold_side_out: float = -5.0
    warm_side_out: float = 35.0
    warm_side_in: float = 30.0


class HeatPump(AbstractTechnology):
    """
    Clustered heat pump for modeling power flows with variable
    temperature levels.

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
        ref_cop: COPReference = None,
        thermal_power_limit: Investment | float = None,
        electrical_power_limit: Investment | float = None,
        max_temp_primary: float = None,
        min_temp_primary: float = None,
        min_delta_temp_primary: float = 5.0,
        max_temp_secondary: float = None,
        min_temp_secondary: float = None,
        min_delta_temp_secondary: float = 5.0,
    ):
        """
        Initialize heat pump component.

        :param thermal_power_limit: Thermal power limit on all
            temperature ranges
        :param cop_0_35: COP for the temperature rise 0°C to 35°C
        :param max_temp_primary: Maximum inlet temperature (°C)
            at the cold side.
        :param min_temp_primary: Minimum outlet temperature (°C)
            at the cold side.
        :param min_delta_temp_primary: Minumum delta (°C) at the cold side.
        :param max_temp_secondary: Maximum outlet temperature (°C)
            at the warm side.
        :param min_temp_secondary: Minimum inlet temperature (°C)
            at the warm side.
        :param min_delta_temp_secondary: Minumum delta (°C) at the warm side.
        """
        super().__init__(name=name)

        if ref_cop is None:
            ref_cop = COPReference()

        self.ref_cop = ref_cop
        self.electrical_power_limit = electrical_power_limit
        self.thermal_power_limit = thermal_power_limit

        self.max_temp_primary = max_temp_primary
        self.min_temp_primary = min_temp_primary
        self.min_delta_temp_primary = min_delta_temp_primary
        self.max_temp_secondary = max_temp_secondary
        self.min_temp_secondary = min_temp_secondary
        self.min_delta_temp_secondary = min_delta_temp_secondary

        # Solph specific parameters
        self.electricity_bus = None
        self.heat_budget_bus = None

        self.q_in = {}
        self.q_out = {}

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        # Add electrical connection
        electricity_carrier = self.location.get_carrier(ElectricityCarrier)

        self.electricity_bus = self.create_solph_node(
            label="electricity",
            node_type=Bus,
            inputs={
                electricity_carrier.distribution: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    },
                    nominal_value=self.electrical_power_limit,
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
            outputs={
                heat_budget_bus: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    },
                    nominal_value=self.thermal_power_limit,
                )
            },
        )

    def establish_interconnections(self) -> None:
        """Add connections to anergy sources."""
        heat_carrier = self.location.get_carrier(HeatCarrier)

        primary_out_levels = heat_carrier.get_levels_between(
            self.min_temp_primary,
            self.max_temp_primary - self.min_delta_temp_primary,
        )
        primary_in_levels = heat_carrier.get_levels_between(
            primary_out_levels[0] + self.min_delta_temp_primary,
            self.max_temp_primary,
        )

        secondary_in_levels = heat_carrier.get_levels_between(
            self.min_temp_secondary,
            self.max_temp_secondary - self.min_delta_temp_secondary,
        )
        secondary_out_levels = heat_carrier.get_levels_between(
            secondary_in_levels[0] + self.min_delta_temp_secondary,
            self.max_temp_secondary,
        )

        for (
            temp_secondary_in,
            temp_secondary_out,
        ) in zip(
            secondary_in_levels,
            secondary_out_levels,
        ):
            self._create_he_node(
                temp_heigh=temp_secondary_out,
                temp_low=temp_secondary_in,
                side="out",
            )

        for (
            temp_primary_out,
            temp_primary_in,
        ) in zip(
            primary_out_levels,
            primary_in_levels,
        ):
            self._create_he_node(
                temp_heigh=temp_primary_in,
                temp_low=temp_primary_out,
                side="in",
            )
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

    def _create_he_node(self, temp_heigh, temp_low, side):
        heat_carrier = self.location.get_carrier(HeatCarrier)

        heat_content = heat_carrier.specific_heat_capacity * (
            temp_heigh - temp_low
        )

        heat_bus_warm = heat_carrier.level_nodes[temp_heigh]
        heat_bus_cold = heat_carrier.level_nodes[temp_low]

        if side == "in":
            q_side = self.create_solph_node(
                label=f"Qin_{temp_heigh:.0f}",
                node_type=Bus,
            )
            self.q_in[int(temp_heigh)] = q_side
            inputs = {
                heat_bus_warm: Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.HEAT,
                    }
                ),
            }
            outputs = {
                q_side: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    }
                ),
                heat_bus_cold: Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.HEAT,
                    }
                ),
            }
        else:
            q_side = self.create_solph_node(
                label=f"Qout_{temp_heigh:.0f}",
                node_type=Bus,
            )
            self.q_out[int(temp_heigh)] = q_side
            inputs = {
                q_side: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    }
                ),
                heat_bus_cold: Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.HEAT,
                    }
                ),
            }
            outputs = {
                heat_bus_warm: Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.HEAT,
                    }
                )
            }

        self.create_solph_node(
            label=f"HE_{side}_{temp_heigh:.0f}",
            node_type=Converter,
            inputs=inputs,
            outputs=outputs,
            conversion_factors={q_side: heat_content},
        )

    def _create_converter_node(
        self,
        temp_primary_out,
        temp_primary_in,
        temp_secondary_in,
        temp_secondary_out,
    ):
        q_in = self.q_in[temp_primary_in]
        q_out = self.q_out[temp_secondary_out]

        cop = calc_cop(
            ref_cop=self.ref_cop,
            temp_primary_in=temp_primary_in,
            temp_primary_out=temp_primary_out,
            temp_secondary_in=temp_secondary_in,
            temp_secondary_out=temp_secondary_out,
        )

        self.create_solph_node(
            label=f"cop_{temp_primary_in:.0f}_{temp_secondary_out:.0f}",
            node_type=Converter,
            inputs={
                q_in: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    }
                ),
                self.electricity_bus: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    }
                ),
                self.heat_budget_bus: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    }
                ),
            },
            outputs={
                q_out: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    }
                ),
            },
            conversion_factors={
                self.electricity_bus: 1 / cop,
                self.heat_budget_bus: 1,
                q_in: 1 - 1 / cop,
                q_out: 1,
            },
        )
