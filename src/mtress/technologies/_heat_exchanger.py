"""This module provides a class representing an air heat exchanger."""

from typing import Optional
import numpy as np

from oemof.solph import Bus, Flow, Investment
from oemof.solph._plumbing import sequence
from oemof.solph.components import Converter, Sink, Source
from pyomo import environ as po

from .._energy_system import EnergySystem as mtress_EnergySystem
from .._data_handler import TimeseriesSpecifier, TimeseriesType
from .._base_mtress_nodes import AbstractTechnology
from .._location import Location
from ..carriers import HeatCarrier

from .._constants import EnergyType


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
        label,
        reservoir_temperature: TimeseriesSpecifier,
        nominal_power: Investment | float,
        minimum_working_temperature: float,
        maximum_working_temperature: float,
        minimum_delta: float,
        conductivity_gain_factor: float | None,
        non_thermal_gains: TimeseriesSpecifier,
        working_rate: TimeseriesSpecifier,
        revenue: TimeseriesSpecifier,
        parent_node,
        custom_properties,
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
        super().__init__(
            label=label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

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

        self.specific_heat_capacity = 1.161

        self._io_converter = {}

        self.__build_core()

    def __build_core(self):
        self.node_t_max = self.subnode(
            Bus,
            local_name=f"T_max",
            custom_properties={
                "temperature": self.maximum_working_temperature,
                "preliminary": "max",
            },
        )

        self.node_t_min = self.subnode(
            Bus,
            local_name=f"T_min",
            custom_properties={
                "temperature": self.minimum_working_temperature,
                "preliminary": "min",
            },
        )

        self.inbound_interfaces[EnergyType.HEAT] = []
        self.outbound_interfaces[EnergyType.HEAT] = []

    @property
    def reservoir_temperature(self):
        return self._reservoir_temperature

    @reservoir_temperature.setter
    def reservoir_temperature(self, value):
        self._reservoir_temperature = sequence(value)

    def _build_core_sink(self):
        self.inbound_interfaces[EnergyType.HEAT].append(self.node_t_max)
        self.outbound_interfaces[EnergyType.HEAT].append(self.node_t_min)

    def _build_core_source(self):
        self.inbound_interfaces[EnergyType.HEAT].append(self.node_t_min)
        self.outbound_interfaces[EnergyType.HEAT].append(self.node_t_max)

        self._bus_source = self.subnode(
            Bus,
            local_name="heat_source",
        )

        self._heat_reservoir = self.subnode(
            Source,
            local_name="source_reservoir",
            outputs={
                self._bus_source: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    },
                    nominal_capacity=self.nominal_power,
                    variable_costs=self.working_rate,
                )
            },
        )

        self._bus_utilisation = self.subnode(
            Bus,
            local_name="utilisation",
        )

        self._source_utilisation = self.subnode(
            Source,
            local_name="source_utilisation",
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
        self._update_source_converters()

    def _add_source_converter(self, cold_bus: Bus, warm_bus: Bus) -> Converter:
        return self.subnode(
            Converter,
            local_name=f"source_{warm_bus.custom_properties['temperature']}",
            inputs={
                self._bus_source: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    },
                    nominal_capacity=self.nominal_power,
                ),
                cold_bus: Flow(
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
                warm_bus: Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.HEAT,
                    }
                )
            },
        )

    def _update_source_converters(self) -> None:
        for cold_bus in self.inbound_interfaces[EnergyType.HEAT]:
            for warm_bus in self.outbound_interfaces[EnergyType.HEAT]:
                t_cold = cold_bus.custom_properties["temperature"]
                t_warm = warm_bus.custom_properties["temperature"]
                if (t_cold < t_warm < self.reservoir_temperature.max()
                    and not (
                        t_warm
                        > self.maximum_working_temperature
                        or t_cold
                        < self.minimum_working_temperature
                    )
                ):
                    if (cold_bus, warm_bus) not in self._io_converter:
                        self._io_converter[(cold_bus, warm_bus)] = (
                            self._add_source_converter(
                                cold_bus,
                                warm_bus,
                            )
                        )
                if (cold_bus, warm_bus) in self._io_converter:
                    self._update_source_gains(cold_bus, warm_bus)

    def _update_source_gains(self, cold_bus: Bus, warm_bus: Bus) -> None:

        converter = self._io_converter[(cold_bus, warm_bus)]
        warm_temperature = warm_bus.custom_properties["temperature"]
        cold_temperature = cold_bus.custom_properties["temperature"]

        if (self.minimum_working_temperature
            <= cold_temperature
            < warm_temperature
            <= self.maximum_working_temperature
        ):
            gains = self._normalised_gains(warm_temperature)
        else:
            gains = np.zeros(len(self.reservoir_temperature))
        heat_factor = self.specific_heat_capacity * (
            warm_temperature - cold_temperature
        )
        if len(gains) > 1:
            inverted_gains = np.array(
                [1 / g if g > 0 else 1 for g in gains]
            )
        else:
            g = gains.value
            inverted_gains = 1 / g if g > 0 else 1

        converter.conversion_factors[self._bus_source] = heat_factor
        converter.conversion_factors[self._bus_utilisation] = (
            heat_factor * inverted_gains
        )
        converter.inputs[self._bus_source].max = gains

        pass

    def _establish_interconnections(self):
        """Shared establish interconnection code for all HeatExchangers.

        This does not implement establish_interconnections,
        so that the class stays abstract.
        """

        self.reservoir_temperature = self._energy_system.data.get_timeseries(
            self.reservoir_temperature,
            kind=TimeseriesType.INTERVAL,
        )

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
        elif self.reservoir_temperature.size is not None:
            # This means full power step at reservoir_temperature.
            # Only makes sense when non_thermal_gains are zero (see above).
            return [
                0 if temperature > t else 1 for t in self.reservoir_temperature
            ]
        else:
            t = self.reservoir_temperature.value
            return sequence(0 if temperature > t else 1)

    def _define_source(self):
        if isinstance(self._energy_system, mtress_EnergySystem):
            self._heat_reservoir.outputs[self._bus_source].variable_costs = (
                self._energy_system.data.get_timeseries(
                    self.working_rate,
                    kind=TimeseriesType.INTERVAL,
                )
            )
        if isinstance(self._parent, Location):
            heat_carrier = self._parent.get_carrier(HeatCarrier)

            highest_warm_level, _ = heat_carrier.get_surrounding_levels(
                self.maximum_working_temperature,
            )

            _, cold_level = heat_carrier.get_surrounding_levels(
                self.minimum_working_temperature
            )
            _, lowest_warm_level = heat_carrier.get_surrounding_levels(
                max(
                    min(
                        min(self.reservoir_temperature),
                        self.minimum_working_temperature,
                    ),
                    (cold_level + self.minimum_delta),
                )
            )

            active_levels = sorted(
                heat_carrier.levels[
                    heat_carrier.levels.index(
                        lowest_warm_level
                    ) : heat_carrier.levels.index(highest_warm_level)
                    + 1
                ],
                reverse=True,
            )

            for (
                cold_temperature,
                warm_temperature,
            ) in zip(active_levels[1:] + [cold_level], active_levels):
                heat_bus_warm_source = heat_carrier.level_nodes[
                    warm_temperature
                ]
                heat_bus_cold_source = heat_carrier.level_nodes[
                    cold_temperature
                ]

    def _sink_constraints(self):
        pass

    def _source_constraints(self):
        model = self._energy_system.model
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
                        self._energy_system.data.get_timeseries(
                            self.revenue,
                            kind=TimeseriesType.INTERVAL,
                        )
                    ),
                )
            },
        )

        highest_warm_level, _ = heat_carrier.get_surrounding_levels(
            self.maximum_working_temperature
        )

        _, lowest_warm_level = heat_carrier.get_surrounding_levels(
            max(
                min(self.reservoir_temperature),
                self.minimum_working_temperature,
            )
        )

        active_levels = sorted(
            heat_carrier.levels[
                heat_carrier.levels.index(
                    lowest_warm_level
                ) : heat_carrier.levels.index(highest_warm_level)
                + 1
            ],
            reverse=True,
        )

        for i in range(len(active_levels) - 1):
            warm_level = active_levels[i]
            cold_level = active_levels[i + 1]

            heat_content = heat_carrier.specific_heat_capacity * (
                warm_level - cold_level
            )

            heat_bus_warm_sink = heat_carrier.level_nodes[warm_level]
            heat_bus_cold_sink = heat_carrier.level_nodes[cold_level]

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
                        maximum=internal_sequence,
                        nominal_capacity=self.nominal_power,
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
        label,
        reservoir_temperature: TimeseriesSpecifier,
        nominal_power: Investment | float,
        minimum_working_temperature: float = 0,
        maximum_working_temperature: float = 100,
        minimum_delta: float = 1.0,
        conductivity_gain_factor: float | None = None,
        non_thermal_gains: Optional[TimeseriesSpecifier] = 0,
        working_rate: Optional[TimeseriesSpecifier] = 0,
        parent_node=None,
        custom_properties=None,
    ):

        super().__init__(
            label=label,
            reservoir_temperature=reservoir_temperature,
            nominal_power=nominal_power,
            minimum_working_temperature=minimum_working_temperature,
            maximum_working_temperature=maximum_working_temperature,
            minimum_delta=minimum_delta,
            conductivity_gain_factor=conductivity_gain_factor,
            non_thermal_gains=non_thermal_gains,
            working_rate=working_rate,
            revenue=None,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        # Solph model interfaces
        self._bus_source = None

        self._build_core_source()

    def establish_interconnections(self) -> None:
        self._establish_interconnections()
        self._define_source()

    def add_constraints(self) -> None:
        """Add constraints to the model."""
        self._source_constraints()


class HeatSink(AbstactHeatExchanger):

    def __init__(
        self,
        label: str,
        reservoir_temperature: TimeseriesSpecifier,
        nominal_power: Investment | float,
        minimum_working_temperature: float = 0,
        maximum_working_temperature: float = 100,
        minimum_delta: float = 1.0,
        conductivity_gain_factor: float | None = None,
        non_thermal_gains: Optional[TimeseriesSpecifier] = 0,
        revenue: Optional[TimeseriesSpecifier] = 0,
        parent_node=None,
        custom_properties=None,
    ):

        super().__init__(
            label=label,
            reservoir_temperature=reservoir_temperature,
            nominal_power=nominal_power,
            minimum_working_temperature=minimum_working_temperature,
            maximum_working_temperature=maximum_working_temperature,
            minimum_delta=minimum_delta,
            conductivity_gain_factor=conductivity_gain_factor,
            non_thermal_gains=non_thermal_gains,
            working_rate=None,
            revenue=revenue,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        # Solph model interfaces
        self._bus_sink = None

        self._build_core_sink()

    def establish_interconnections(self) -> None:
        self._establish_interconnections()
        self._define_sink()

    def add_constraints(self, model):
        self._sink_constraints()


class HeatExchanger(AbstactHeatExchanger):

    def __init__(
        self,
        label,
        reservoir_temperature: TimeseriesSpecifier,
        nominal_power: Investment | float,
        minimum_working_temperature: float = 0,
        maximum_working_temperature: float = 100,
        minimum_delta: float = 1.0,
        conductivity_gain_factor: float | None = None,
        non_thermal_gains: Optional[TimeseriesSpecifier] = 0,
        working_rate: Optional[TimeseriesSpecifier] = 0,
        revenue: Optional[TimeseriesSpecifier] = 0,
        parent_node=None,
        custom_properties=None,
    ):

        super().__init__(
            label=label,
            reservoir_temperature=reservoir_temperature,
            nominal_power=nominal_power,
            minimum_working_temperature=minimum_working_temperature,
            maximum_working_temperature=maximum_working_temperature,
            conductivity_gain_factor=conductivity_gain_factor,
            non_thermal_gains=non_thermal_gains,
            minimum_delta=minimum_delta,
            working_rate=working_rate,
            revenue=revenue,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        # Solph model interfaces
        self._bus_source = None
        self._bus_sink = None

        self._build_core_sink()
        self._build_core_source()

    def establish_interconnections(self) -> None:
        self._establish_interconnections()
        self._define_sink()
        self._define_source()

    def add_constraints(self) -> None:
        """Add constraints to the model."""
        self._sink_constraints()
        self._source_constraints()
