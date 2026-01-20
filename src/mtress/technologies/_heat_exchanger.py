"""This module provides a class representing an air heat exchanger."""

import logging
from typing import Optional
import numpy as np

from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Converter, Sink, Source
from pyomo import environ as po

from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ..carriers import HeatCarrier
from ._abstract_technology import AbstractTechnology

from .._constants import EnergyType


_LOGGER = logging.getLogger(__name__)


class AbstactHeatExchanger(AbstractTechnology):
    """
    Heat exchanger (HE)

    Functionality: Holds a time series of both the temperature and the
        power limit that can be drawn from the source and/or expelled
        to the sink.

    Procedure: Define the type of HE:
        1. Source:
            house_1.add(
                technologies.HeatSource(.....)

        2. Sink:
            house_1.add(
                technologies.HeatSink(.....)

        3. Source and Sink:
            house_1.add(
                technologies.HeatExchanger(.....)

    """

    def __init__(
        self,
        name: str,
        reservoir_temperature: TimeseriesSpecifier,
        minimum_working_temperature: float = 0,
        maximum_working_temperature: float = 0,
        nominal_power: Investment | float | None = None,
        minimum_delta: float = 1.0,
        conductivity_gain_factor: float | None = None,
        non_thermal_gains: Optional[TimeseriesSpecifier] = 0,
        working_rate: Optional[TimeseriesSpecifier] = 0,
        revenue: Optional[TimeseriesSpecifier] = 0,
    ):
        """
        Initialize heat exchanger to draw or expel energy from a source

        :param name: Name of the component.
        :param reservoir_temperature: Temperature of the reservoir (in °C)
        :param minimum_working_temperature: Minimum temperature limit (in °C)
        :param maximum_working_temperature: Maximum temperature limit (in °C)
        :param nominal_power: Nominal power of the heat exchanger (in W),
            is treated as a power limit.
        :param minimum_delta: Specifies the delta between the primary and
            secondary sides of the HE (in °C), needs to be > 1 °C
        :param conductivity_gain_factor: Gains (in nominal_power/K)
        :param non_thermal_gains: Additional gains (relative to nominal power)
        :param working_rate: Working price of imported heat in currency/Wh
        :param revenue: Revenue from heat exported to a sink in currency/Wh


        The heat is (partly) taken from the reservoir. If there are no
        non_thermal_gains, its temperatre needs to be above (strictly greater)
        the target temperature.
        """
        super().__init__(name=name)

        self.reservoir_temperature = reservoir_temperature
        self.minimum_working_temperature = minimum_working_temperature
        self.maximum_working_temperature = maximum_working_temperature
        self.nominal_power = nominal_power
        self.minimum_delta = minimum_delta
        self.conductivity_gain_factor = conductivity_gain_factor
        self.non_thermal_gains = non_thermal_gains
        self.working_rate = working_rate
        self.revenue = revenue

        if minimum_delta < 1:
            raise ValueError("minimum_delta has to be > 1 °C")

        if (
            np.array(self.non_thermal_gains).max() != 0
            and not self.conductivity_gain_factor
        ):
            raise ValueError(
                "AbstactHeatExchanger.non_thermal_gains only"
                " makes sense when conductivity is also set."
            )

    def _build_core(self):
        self.reservoir_temperature = self._solph_model.data.get_timeseries(
            self.reservoir_temperature,
            kind=TimeseriesType.INTERVAL,
        )

        self.heat_carrier = self.location.get_carrier(HeatCarrier)

    def _normalised_gains(self, temperature):
        if self.conductivity_gain_factor is not None:
            unbound_gains = np.zeros(len(self.reservoir_temperature))
            # We want a copy but do not know if self.non_thermal_gains
            # is a scalar or an array.
            unbound_gains += self.non_thermal_gains

            unbound_gains += (
                self.reservoir_temperature - temperature
            ) * self.conductivity_gain_factor
            return np.clip(unbound_gains, 0, 1)
        else:
            # This means full power step at reservoir_temperature.
            # Only makes sense when non_thermal_gains are zero (see above).
            return [
                0 if temperature > t else 1 for t in self.reservoir_temperature
            ]

    def _define_source(self):
        self._bus_source = _bus_source = self.create_solph_node(
            label="heat_source",
            node_type=Bus,
        )

        self._heat_reservoir = self.create_solph_node(
            label="source_reservoir",
            node_type=Source,
            outputs={
                _bus_source: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    },
                    nominal_value=self.nominal_power,
                    variable_costs=self._solph_model.data.get_timeseries(
                        self.working_rate,
                        kind=TimeseriesType.INTERVAL,
                    ),
                )
            },
        )

        self._bus_utilisation = self.create_solph_node(
            label="utilisation",
            node_type=Bus,
        )

        self._source_utilisation = self.create_solph_node(
            label="source_utilisation",
            node_type=Source,
            outputs={
                self._bus_utilisation: Flow(
                    nominal_capacity=self.nominal_power,
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    },
                )
            },
        )

        if self.autoconnect:
            highest_warm_level, _ = self.heat_carrier.get_surrounding_levels(
                self.maximum_working_temperature,
            )

            _, cold_level = self.heat_carrier.get_surrounding_levels(
                self.minimum_working_temperature
            )
            _, lowest_warm_level = self.heat_carrier.get_surrounding_levels(
                max(
                    min(
                        min(self.reservoir_temperature),
                        self.minimum_working_temperature,
                    ),
                    (cold_level + self.minimum_delta),
                )
            )

            active_levels = sorted(
                self.heat_carrier.levels[
                    self.heat_carrier.levels.index(
                        lowest_warm_level
                    ) : self.heat_carrier.levels.index(highest_warm_level)
                    + 1
                ],
                reverse=True,
            )

            for (
                cold_temperature,
                warm_temperature,
            ) in zip(active_levels[1:] + [cold_level], active_levels):
                heat_bus_warm_source = self.heat_carrier.level_nodes[
                    warm_temperature
                ]
                heat_bus_cold_source = self.heat_carrier.level_nodes[
                    cold_temperature
                ]

                gains = self._normalised_gains(warm_temperature)
                heat_factor = self.heat_carrier.specific_heat_capacity * (
                    warm_temperature - cold_temperature
                )
                inverted_gains = np.array(
                    [1 / g if g > 0 else 1 for g in gains]
                )

                self.create_solph_node(
                    label=f"source_{warm_temperature}",
                    node_type=Converter,
                    inputs={
                        _bus_source: Flow(
                            custom_properties={
                                "unit": "W",
                                "energy_type": EnergyType.HEAT,
                            },
                            nominal_value=self.nominal_power,
                            max=gains,
                        ),
                        heat_bus_cold_source: Flow(
                            custom_properties={
                                "unit": "kg/h",
                                "energy_type": EnergyType.HEAT,
                            }
                        ),
                        self._bus_utilisation: Flow(
                            custom_properties={
                                "unit": "kg/h",
                                "energy_type": EnergyType.HEAT,
                            }
                        ),
                    },
                    outputs={
                        heat_bus_warm_source: Flow(
                            custom_properties={
                                "unit": "kg/h",
                                "energy_type": EnergyType.HEAT,
                            }
                        )
                    },
                    conversion_factors={
                        _bus_source: heat_factor,
                        self._bus_utilisation: heat_factor * inverted_gains,
                        heat_bus_cold_source: 1,
                        heat_bus_warm_source: 1,
                    },
                )

    def _source_constraints(self):
        model = self._solph_model.model
        name = str(self.node) + "_power_limit"

        def _equate_flow_groups_rule(m):
            for ts in m.TIMESTEPS:
                expr = (
                    m.flow[self._source_utilisation, self._bus_utilisation, ts]
                    >= m.flow[self._heat_reservoir, self._bus_source, ts]
                )
                getattr(m, name).add(ts, expr)

        setattr(
            model,
            name,
            po.Constraint(model.TIMESTEPS, noruleinit=True),
        )
        setattr(
            model,
            name + "_build",
            po.BuildAction(rule=_equate_flow_groups_rule),
        )

    def _define_sink(self):
        self._bus_sink = _bus_sink = self.create_solph_node(
            label="output",
            node_type=Bus,
        )

        self.create_solph_node(
            label="sink",
            node_type=Sink,
            inputs={
                _bus_sink: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    },
                    variable_costs=-(
                        self._solph_model.data.get_timeseries(
                            self.revenue,
                            kind=TimeseriesType.INTERVAL,
                        )
                    ),
                )
            },
        )

        highest_warm_level, _ = self.heat_carrier.get_surrounding_levels(
            self.maximum_working_temperature
        )

        _, lowest_warm_level = self.heat_carrier.get_surrounding_levels(
            max(
                min(self.reservoir_temperature),
                self.minimum_working_temperature,
            )
        )

        active_levels = sorted(
            self.heat_carrier.levels[
                self.heat_carrier.levels.index(
                    lowest_warm_level
                ) : self.heat_carrier.levels.index(highest_warm_level)
                + 1
            ],
            reverse=True,
        )

        for i in range(len(active_levels) - 1):
            warm_level = active_levels[i]
            cold_level = active_levels[i + 1]

            heat_content = self.heat_carrier.specific_heat_capacity * (
                warm_level - cold_level
            )

            heat_bus_warm_sink = self.heat_carrier.level_nodes[warm_level]
            heat_bus_cold_sink = self.heat_carrier.level_nodes[cold_level]

            internal_sequence = [
                1 if temp <= cold_level else 0
                for temp in self.reservoir_temperature
            ]

            self.create_solph_node(
                label=f"sink_{warm_level}",
                node_type=Converter,
                inputs={
                    heat_bus_warm_sink: Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.HEAT,
                        }
                    ),
                },
                outputs={
                    heat_bus_cold_sink: Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.HEAT,
                        }
                    ),
                    _bus_sink: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.HEAT,
                        },
                        max=internal_sequence,
                        nominal_value=self.nominal_power,
                    ),
                },
                conversion_factors={
                    _bus_sink: heat_content,
                    heat_bus_cold_sink: 1,
                    heat_bus_warm_sink: 1,
                },
            )


class HeatSource(AbstactHeatExchanger):

    def __init__(
        self,
        name: str,
        reservoir_temperature: TimeseriesSpecifier,
        minimum_working_temperature: float = 0,
        maximum_working_temperature: float = 0,
        nominal_power: Investment | float | None = None,
        minimum_delta: float = 1.0,
        conductivity_gain_factor: float | None = None,
        non_thermal_gains: Optional[TimeseriesSpecifier] = 0,
        working_rate: Optional[TimeseriesSpecifier] = 0,
    ):

        super().__init__(
            name=name,
            reservoir_temperature=reservoir_temperature,
            minimum_working_temperature=minimum_working_temperature,
            maximum_working_temperature=maximum_working_temperature,
            nominal_power=nominal_power,
            minimum_delta=minimum_delta,
            conductivity_gain_factor=conductivity_gain_factor,
            non_thermal_gains=non_thermal_gains,
            working_rate=working_rate,
        )

        # Solph model interfaces
        self._bus_source = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()
        self._build_core()

    def establish_interconnections(self) -> None:
        self._define_source()

    def add_constraints(self) -> None:
        """Add constraints to the model."""
        self._source_constraints()


class HeatSink(AbstactHeatExchanger):

    def __init__(
        self,
        name: str,
        reservoir_temperature: TimeseriesSpecifier,
        minimum_working_temperature: float = 0,
        maximum_working_temperature: float = 0,
        nominal_power: Investment | float | None = None,
        minimum_delta: float = 1.0,
        conductivity_gain_factor: float | None = None,
        non_thermal_gains: Optional[TimeseriesSpecifier] = 0,
        revenue: float = 0,
    ):

        super().__init__(
            name=name,
            reservoir_temperature=reservoir_temperature,
            minimum_working_temperature=minimum_working_temperature,
            maximum_working_temperature=maximum_working_temperature,
            nominal_power=nominal_power,
            minimum_delta=minimum_delta,
            conductivity_gain_factor=conductivity_gain_factor,
            non_thermal_gains=non_thermal_gains,
            revenue=revenue,
        )

        # Solph model interfaces
        self._bus_sink = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        self._build_core()

    def establish_interconnections(self) -> None:
        self._define_sink()


class HeatExchanger(AbstactHeatExchanger):

    def __init__(
        self,
        name: str,
        reservoir_temperature: TimeseriesSpecifier,
        nominal_power: Investment | float,
        minimum_working_temperature: float = 0,
        maximum_working_temperature: float = 0,
        minimum_delta: float = 1.0,
        conductivity_gain_factor: float | None = None,
        non_thermal_gains: Optional[TimeseriesSpecifier] = 0,
    ):

        super().__init__(
            name=name,
            reservoir_temperature=reservoir_temperature,
            minimum_working_temperature=minimum_working_temperature,
            maximum_working_temperature=maximum_working_temperature,
            nominal_power=nominal_power,
            conductivity_gain_factor=conductivity_gain_factor,
            non_thermal_gains=non_thermal_gains,
            minimum_delta=minimum_delta,
        )

        # Solph model interfaces
        self._bus_source = None
        self._bus_sink = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()
        self._build_core()

    def establish_interconnections(self) -> None:
        self._define_source()
        self._define_sink()

    def add_constraints(self) -> None:
        """Add constraints to the model."""
        self._source_constraints()
