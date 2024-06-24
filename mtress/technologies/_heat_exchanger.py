"""This module provides a class representing an air heat exchanger."""

import numpy as np
from oemof.solph import Bus, Flow
from oemof.solph.components import Converter, Sink, Source

from .._abstract_component import AbstractSolphRepresentation
from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ..carriers import HeatCarrier
from ._abstract_technology import AbstractTechnology


class AbstactHeatExchanger(AbstractTechnology, AbstractSolphRepresentation):
    """
    Heat exchanger

    Functionality: Holds a time series of both the temperature and the
        power limit that can be drawn from the source and/or expelled to the sink.

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
        nominal_power: float = None,
        minimum_delta: float = 1.0,
    ):
        """
        Initialize heat exchanger to draw or expel energy from a source

        :param name: Name of the component.
        :param nominal_power: Nominal power of the heat exchanger (in W), default to None.
        :param reservoir_temperature: Reference to air temperature time series
        """
        super().__init__(name=name)

        self.reservoir_temperature = reservoir_temperature
        self.minimum_working_temperature = minimum_working_temperature
        self.maximum_working_temperature = maximum_working_temperature
        self.nominal_power = nominal_power
        self.minimum_delta = minimum_delta

    def _build_core(self):
        self.reservoir_temperature = self._solph_model.data.get_timeseries(
            self.reservoir_temperature,
            kind=TimeseriesType.INTERVAL,
        )

        self.heat_carrier = self.location.get_carrier(HeatCarrier)

    def _define_source(self):
        self._build_core()

        highest_warm_level, _ = self.heat_carrier.get_surrounding_levels(
            min(max(self.reservoir_temperature), self.maximum_working_temperature)
        )

        _, cold_level = self.heat_carrier.get_surrounding_levels(
            self.minimum_working_temperature
        )
        _, lowest_warm_level = self.heat_carrier.get_surrounding_levels(
            max(
                min(min(self.reservoir_temperature), self.minimum_working_temperature),
                (cold_level + self.minimum_delta),
            )
        )

        self._bus_source = _bus_source = self.create_solph_node(
            label="input",
            node_type=Bus,
        )

        self.create_solph_node(
            label="source",
            node_type=Source,
            outputs={_bus_source: Flow()},
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
            ratio = (cold_temperature - self.heat_carrier.reference) / (
                warm_temperature - self.heat_carrier.reference
            )

            heat_bus_warm_source = self.heat_carrier.level_nodes[warm_temperature]
            heat_bus_cold_source = self.heat_carrier.level_nodes[cold_temperature]

            internal_sequence = [
                1 if temp >= warm_temperature else 0
                for temp in self.reservoir_temperature
            ]

            self.create_solph_node(
                label=f"source_{warm_temperature}",
                node_type=Converter,
                inputs={
                    _bus_source: Flow(
                        max=internal_sequence, nominal_value=self.nominal_power
                    ),
                    heat_bus_cold_source: Flow(),
                },
                outputs={heat_bus_warm_source: Flow()},
                conversion_factors={
                    _bus_source: (1 - ratio),
                    heat_bus_cold_source: ratio,
                    heat_bus_warm_source: 1,
                },
            )

    def _define_sink(self):
        self._build_core()

        highest_warm_level, _ = self.heat_carrier.get_surrounding_levels(
            self.maximum_working_temperature
        )

        _, lowest_warm_level = self.heat_carrier.get_surrounding_levels(
            max(
                min(self.reservoir_temperature),
                self.minimum_working_temperature,
            )
        )

        self._bus_sink = _bus_sink = self.create_solph_node(
            label="output",
            node_type=Bus,
        )

        self.create_solph_node(
            label="sink",
            node_type=Sink,
            inputs={_bus_sink: Flow()},
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

            ratio = (cold_level - self.heat_carrier.reference) / (
                warm_level - self.heat_carrier.reference
            )

            heat_bus_warm_sink = self.heat_carrier.level_nodes[warm_level]
            heat_bus_cold_sink = self.heat_carrier.level_nodes[cold_level]

            internal_sequence = [
                1 if temp <= cold_level else 0 for temp in self.reservoir_temperature
            ]

            self.create_solph_node(
                label=f"sink_{warm_level}",
                node_type=Converter,
                inputs={
                    heat_bus_warm_sink: Flow(),
                },
                outputs={
                    heat_bus_cold_sink: Flow(),
                    _bus_sink: Flow(
                        max=internal_sequence, nominal_value=self.nominal_power
                    ),
                },
                conversion_factors={
                    _bus_sink: (1 - ratio),
                    heat_bus_cold_sink: ratio,
                    heat_bus_warm_sink: 1,
                },
            )

        return


class HeatSource(AbstactHeatExchanger):
    def __init__(
        self,
        name: str,
        reservoir_temperature: TimeseriesSpecifier,
        minimum_working_temperature: float = 0,
        maximum_working_temperature: float = 0,
        nominal_power: float = None,
        minimum_delta: float = 1.0,
    ):

        super().__init__(
            name=name,
            reservoir_temperature=reservoir_temperature,
            minimum_working_temperature=minimum_working_temperature,
            maximum_working_temperature=maximum_working_temperature,
            nominal_power=nominal_power,
            minimum_delta=minimum_delta,
        )

        # Solph model interfaces
        self._bus_source = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        self._define_source()


class HeatSink(AbstactHeatExchanger):
    def __init__(
        self,
        name: str,
        reservoir_temperature: TimeseriesSpecifier,
        minimum_working_temperature: float = 0,
        maximum_working_temperature: float = 0,
        nominal_power: float = None,
        minimum_delta: float = 1.0,
    ):

        super().__init__(
            name=name,
            reservoir_temperature=reservoir_temperature,
            minimum_working_temperature=minimum_working_temperature,
            maximum_working_temperature=maximum_working_temperature,
            nominal_power=nominal_power,
            minimum_delta=minimum_delta,
        )

        # Solph model interfaces
        self._bus_sink = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        self._define_sink()


class HeatExchanger(AbstactHeatExchanger):
    def __init__(
        self,
        name: str,
        reservoir_temperature: TimeseriesSpecifier,
        minimum_working_temperature: float = 0,
        maximum_working_temperature: float = 0,
        nominal_power: float = None,
        minimum_delta: float = 1.0,
    ):

        super().__init__(
            name=name,
            reservoir_temperature=reservoir_temperature,
            minimum_working_temperature=minimum_working_temperature,
            maximum_working_temperature=maximum_working_temperature,
            nominal_power=nominal_power,
            minimum_delta=minimum_delta,
        )

        # Solph model interfaces
        self._bus_source = None
        self._bus_sink = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        self._define_source()
        self._define_sink()
