"""This module provides a class representing an air heat exchanger."""

from typing import Optional
import numpy as np
import warnings

from collections.abc import Iterable

from oemof.solph import Bus, Investment
from oemof.solph._plumbing import _FakeSequence
from oemof.solph._plumbing import Apply
from oemof.solph._plumbing import sequence
from oemof.solph.components import Converter, Sink, Source
from pyomo import environ as po

from .._energy_system import EnergySystem as mtress_EnergySystem
from .._data_handler import TimeseriesSpecifier, TimeseriesType
from .._base_mtress_nodes import AbstractTechnology
from .._location import Location
from ..carriers import HeatCarrier

from .._energy_types import EnergyFlowHeat
from .._energy_types import EnergyQuality
from .._energy_types import EnergyType
from .._energy_types import TemperatureBus
from .._energy_types import MassFlowHeat


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
    reservoir_temperature = Apply(sequence)

    def __init__(
        self,
        label,
        reservoir_temperature: TimeseriesSpecifier,
        nominal_power: Investment | float,
        minimum_working_temperature: float,
        maximum_working_temperature: float,
        minimum_delta_medium: float,
        minimum_delta_reservoir: float,
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
        non_thermal_gains, its temperature needs to be above (strictly greater)
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
        self.minimum_delta_medium = minimum_delta_medium
        self.minimum_delta_reservoir = minimum_delta_reservoir
        self.conductivity_gain_factor = conductivity_gain_factor
        self.non_thermal_gains = non_thermal_gains
        self.working_rate = working_rate
        self.revenue = revenue

        if minimum_delta_medium < 1 or minimum_delta_reservoir < 1:
            raise ValueError("minimum_delta has to be >= 1 °C")

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

    def _establish_interconnections(self):
        """Shared establish interconnection code for all HeatExchangers.

        This does not implement establish_interconnections,
        so that the class stays abstract.
        """
        self.reservoir_temperature = self._energy_system.data.get_timeseries(
            self.reservoir_temperature,
            kind=TimeseriesType.INTERVAL,
        )

    def _align_timeindex_sink(self):
        self._heat_sink.inputs[self._bus_sink].variable_costs = (
            self._energy_system.data.get_timeseries(
                self.revenue,
                kind=TimeseriesType.INTERVAL,
            )
        )

    def _align_timeindex_source(self):
        self._heat_reservoir.outputs[self._bus_source].variable_costs = (
            self._energy_system.data.get_timeseries(
                self.working_rate,
                kind=TimeseriesType.INTERVAL,
            )
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
        elif not isinstance(self.reservoir_temperature, _FakeSequence):
            # This means full power step at reservoir_temperature.
            # Only makes sense when non_thermal_gains are zero (see above).
            return [
                t_low < t_high for t_low, t_high in zip(
                    temperature, self.reservoir_temperature
                )
            ]
        else:
            t = self.reservoir_temperature.value
            if isinstance(temperature, np.ndarray):
                return np.array(temperature > t, dtype=float)
            else:
                return sequence(0 if temperature > t else 1)

    def _sink_constraints(self, model):
        pass

    def _source_constraints(self, model):
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


class HeatSource(AbstactHeatExchanger):

    def __init__(
        self,
        label,
        reservoir_temperature: TimeseriesSpecifier,
        nominal_power: Investment | float,
        minimum_working_temperature: float = 0,
        maximum_working_temperature: float = 100,
        minimum_delta_medium: float = 1.0,
        minimum_delta_reservoir: float = 1.0,
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
            minimum_delta_medium=minimum_delta_medium,
            minimum_delta_reservoir=minimum_delta_reservoir,
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

    def _build_core_source(self):

        #maximum_outlet_temperature = np.amin(
        #    self.maximum_working_temperature,
        #    self.reservoir_temperature - self.minimum_delta_reservoir
        #)

        node_t_max = self.subnode(
            TemperatureBus,
            local_name=f"T_max_source",
            temperature=EnergyQuality(
                value=self.maximum_working_temperature,
                minimum=(
                    self.minimum_working_temperature
                    + self.minimum_delta_medium
                ),
                maximum=self.maximum_working_temperature,
            ),
            specific_heat_capacity=self.specific_heat_capacity,
        )

        node_t_min = self.subnode(
            TemperatureBus,
            local_name=f"T_min_source",
            temperature=EnergyQuality(
                value=self.minimum_working_temperature,
                minimum=self.minimum_working_temperature,
                maximum=(
                    self.maximum_working_temperature
                    - self.minimum_delta_medium
                ),
            ),
            specific_heat_capacity=self.specific_heat_capacity,
        )
        
        self.inbound_interfaces.append(node_t_min)
        self.outbound_interfaces.append(node_t_max)

        self._bus_source = self.subnode(
            Bus,
            local_name="heat_source",
        )

        # for absolute normalised power
        self._heat_reservoir = self.subnode(
            Source,
            local_name="source_reservoir",
            outputs={
                self._bus_source: EnergyFlowHeat(
                    nominal_capacity=self.nominal_power,
                    variable_costs=self.working_rate,
                )
            },
        )

        self._bus_utilisation = self.subnode(
            Bus,
            local_name="utilisation",
        )

        # for efficiency normalised power
        self._source_utilisation = self.subnode(
            Source,
            local_name="source_utilisation",
            outputs={
                self._bus_utilisation: EnergyFlowHeat(
                    nominal_capacity=self.nominal_power,
                )
            },
        )
        self._update_source_converters()

    def _add_source_converter(self, cold_bus: Bus, warm_bus: Bus) -> Converter:
        return self.subnode(
            Converter,
            local_name=f"{cold_bus.label[0]}->{warm_bus.label[0]}",
            inputs={
                self._bus_source: EnergyFlowHeat(
                    nominal_capacity=self.nominal_power,
                ),
                cold_bus: MassFlowHeat(),
                self._bus_utilisation: MassFlowHeat(),
            },
            outputs={
                warm_bus: MassFlowHeat(),
            },
        )

    def _update_source_converters(self) -> None:
        for cold_bus in self.inbound_interfaces:
            for warm_bus in self.outbound_interfaces:
                t_cold = cold_bus.custom_properties["temperature"]
                t_warm = warm_bus.custom_properties["temperature"]
                if t_cold.min() < t_warm.max() and (
                    t_warm.min() < self.reservoir_temperature.max()) and not (
                    t_warm.min() > self.maximum_working_temperature
                    or t_cold.max() < self.minimum_working_temperature
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

        if (
            self.minimum_working_temperature
            <= cold_temperature.max() and
            cold_temperature.min()
            < warm_temperature.max() and
            warm_temperature.min()
            <= self.maximum_working_temperature
        ):
            gains = self._normalised_gains(warm_temperature)
        else:
            gains = np.zeros(len(self.reservoir_temperature))
        heat_factor = self.specific_heat_capacity * (
            warm_temperature - cold_temperature
        )
        if isinstance(gains, Iterable):
            inverted_gains = np.array([1 / g if g > 0 else 1 for g in gains])
        else:
            inverted_gains = 1 / gains if gains > 0 else 1

        converter.conversion_factors[self._bus_source] = sequence(heat_factor)
        converter.conversion_factors[self._bus_utilisation] = sequence(
            heat_factor * inverted_gains
        )
        converter.inputs[self._bus_source].max = sequence(gains)


    def establish_interconnections(self) -> None:
        self._establish_interconnections()

        heat_carrier: HeatCarrier = self.parent.get_carrier(HeatCarrier)

        for in_node in self.inbound_interfaces:
            upstream_node = heat_carrier.nodes_to_connect(in_node)[0]
            in_node.inputs[upstream_node] = MassFlowHeat()
            in_node.temperature = upstream_node.temperature

        for out_node in self.outbound_interfaces:
            downstream_node = heat_carrier.nodes_to_connect(out_node)[0]
            out_node.outputs[downstream_node] = MassFlowHeat()
            out_node.temperature = downstream_node.temperature

        self._update_source_converters()

    def add_constraints(self, model) -> None:
        """Add constraints to the model."""
        self._source_constraints(model)


class HeatSink(AbstactHeatExchanger):

    def __init__(
        self,
        label: str,
        reservoir_temperature: TimeseriesSpecifier,
        nominal_power: Investment | float,
        minimum_working_temperature: float = 0,
        maximum_working_temperature: float = 100,
        minimum_delta_medium: float = 1.0,
        minimum_delta_reservoir: float = 1.0,
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
            minimum_delta_medium=minimum_delta_medium,
            minimum_delta_reservoir=minimum_delta_reservoir,
            conductivity_gain_factor=None,
            non_thermal_gains=0,
            working_rate=None,
            revenue=revenue,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        # Solph model interfaces
        self._bus_sink = None

        self._build_core_sink()

    def _build_core_sink(self):
        node_t_max = self.subnode(
            TemperatureBus,
            local_name=f"T_max_sink",
            temperature=EnergyQuality(
                value=self.maximum_working_temperature,
                minimum=self.minimum_working_temperature + self.minimum_delta_medium,
                maximum=self.maximum_working_temperature,
            ),
            specific_heat_capacity=self.specific_heat_capacity,
        )

        node_t_min = self.subnode(
            TemperatureBus,
            local_name=f"T_min_sink",
            temperature=EnergyQuality(
                value=self.minimum_working_temperature,
                minimum=self.minimum_working_temperature,
                maximum=self.maximum_working_temperature - self.minimum_delta_medium,
                fixed=False,
            ),
            specific_heat_capacity=self.specific_heat_capacity,
        )

        self.inbound_interfaces.append(node_t_max)
        self.outbound_interfaces.append(node_t_min)

        self._bus_sink = self.create_solph_node(
            label="output",
            node_type=Bus,
        )

        self._heat_sink = self.create_solph_node(
            label="sink",
            node_type=Sink,
            inputs={
                self._bus_sink: EnergyFlowHeat(
                    variable_costs=-self.revenue,
                )
            },
        )

        self._update_source_converters()


    def _add_sink_converter(self, cold_bus: Bus, warm_bus: Bus) -> Converter:
        return self.subnode(
            Converter,
            local_name=f"sink_{warm_bus.label[0]}",
            inputs={
                warm_bus: MassFlowHeat(),
            },
            outputs={
                cold_bus: MassFlowHeat(),
                self._bus_sink: EnergyFlowHeat(
                    nominal_capacity=self.nominal_power,
                ),
            },
        )

    def _update_sink_converters(self) -> None:
        for warm_bus in self.inbound_interfaces[HeatCarrier]:
            for cold_bus in self.outbound_interfaces[HeatCarrier]:
                t_cold = cold_bus.custom_properties["temperature"]
                t_warm = warm_bus.custom_properties["temperature"]
                if self.reservoir_temperature.min() < t_cold.max() and (
                    t_cold.min() < t_warm.max()) and not (
                    t_warm.min() > self.maximum_working_temperature
                    or t_cold < self.minimum_working_temperature
                ):
                    if (warm_bus, cold_bus) not in self._io_converter:
                        self._io_converter[(cold_bus, warm_bus)] = (
                            self._add_source_converter(
                                cold_bus,
                                warm_bus,
                            )
                        )
                if (cold_bus, warm_bus) in self._io_converter:
                    self._update_sink_losses(warm_bus, cold_bus)

    def _update_sink_losses(self, warm_bus: Bus, cold_bus: Bus) -> None:
        converter = self._io_converter[(warm_bus, cold_bus)]
        warm_temperature = warm_bus.custom_properties["temperature"]
        cold_temperature = cold_bus.custom_properties["temperature"]

        if (
            self.minimum_working_temperature
            <= cold_temperature
            < warm_temperature
            <= self.maximum_working_temperature
        ):
            losses = [
                1 if t <= cold_temperature else 0
                for t in self.reservoir_temperature
            ]
        else:
            losses = np.zeros(len(self.reservoir_temperature))
        heat_factor = self.specific_heat_capacity * (
            warm_temperature - cold_temperature
        )

        converter.conversion_factors[self._bus_sink] = sequence(heat_factor)

        converter.outputs[self._bus_sink].max = losses

    def establish_interconnections(self) -> None:
        self._establish_interconnections()
        self._update_sink_converters()


    def add_constraints(self, model):
        self._sink_constraints(model)
