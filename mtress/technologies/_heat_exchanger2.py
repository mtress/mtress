"""This module provides a class representing an air heat exchanger."""

import numpy as np

from oemof.solph import Bus, Flow
from oemof.solph.components import Source, Converter, Sink

from .._abstract_component import AbstractSolphRepresentation
from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ._abstract_technology import AbstractTechnology, AbstractAnergySource
from ..carriers import HeatCarrier


class HeatExchanger2(AbstractTechnology, AbstractSolphRepresentation):
    """
    Air heat exchanger for e.g. heat pumps.

    Functionality: Air heat exchanger for e.g. heat pumps. Holds a time
        series of both the temperature and the power limit that can be
        drawn from the source.

    Procedure: Create a simple air heat exchanger by doing the following:

        house_1.add_component(
            technologies.AirHeatExchanger(air_temperatures=[3])

    Further documentation regarding anergy found in the class
    AbstractAnergysource.

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
        Initialize air heat exchanger for e.g. heat pumps.

        :param name: Name of the component.
        :param nominal_power: Nominal power of the heat exchanger (in W), default to None.
        :param air_temperatures: Reference to air temperature time series
        """
        super().__init__(name=name)

        self.reservoir_temperature = reservoir_temperature
        self.minimum_working_temperature = minimum_working_temperature
        self.maximum_working_temperature = maximum_working_temperature
        self.nominal_power = nominal_power
        self.minimum_delta = minimum_delta

        # Solph model interfaces
        self._bus_source = None
        self._bus_sink = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        self.reservoir_temperature = self._solph_model.data.get_timeseries(
            self.reservoir_temperature,
            kind=TimeseriesType.INTERVAL,
        )

        self.minimum_working_temperature = 0
        self.maximum_working_temperature = 40

        heat_carrier = self.location.get_carrier(HeatCarrier)

        highest_warm_level_heating, _ = heat_carrier.get_surrounding_levels(
            min(max(self.reservoir_temperature), self.maximum_working_temperature)
        )

        _, cold_level_heating = heat_carrier.get_surrounding_levels(
            self.minimum_working_temperature
        )
        _, lowest_warm_level_heating = heat_carrier.get_surrounding_levels(
            max(
                min(min(self.reservoir_temperature), self.minimum_working_temperature),
                (cold_level_heating + self.minimum_delta),
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

        # self.reservoir_temperature = [10, 15, 18, 20, 21, 22, 25]
        # Heat levels = [0, 5, 10, 20, 30, 40]
        # highest_level = 20
        # lowest_warm_level = 0

        for warm_temperature in heat_carrier.levels[
            heat_carrier.levels.index(
                highest_warm_level_heating
            ) : heat_carrier.levels.index(lowest_warm_level_heating) : -1
        ]:
            ratio = (lowest_warm_level_heating - heat_carrier.reference) / (
                warm_temperature - heat_carrier.reference
            )

            heat_bus_warm_source = heat_carrier.level_nodes[warm_temperature]
            heat_bus_cold_source = heat_carrier.level_nodes[lowest_warm_level_heating]

            self.create_solph_node(
                label=f"converter_{warm_temperature}",
                node_type=Converter,
                inputs={
                    _bus_source: Flow(nominal_value=self.nominal_power),
                    heat_bus_cold_source: Flow(),
                },
                outputs={heat_bus_warm_source: Flow()},
                conversion_factors={
                    _bus_source: (1 - ratio),
                    heat_bus_cold_source: ratio,
                    heat_bus_warm_source: 1,
                },
            )

        # heat_bus_warm_sink, heat_bus_cold_sink, ratio = (
        #     heat_carrier.get_connection_heat_transfer(
        #         self.maximum_temperature, self.reservoir_temperature
        #     )
        # )

        # self._bus_sink = _bus_sink = self.create_solph_node(
        #     label="output",
        #     node_type=Bus,
        # )

        # self.create_solph_node(
        #     label="sink",
        #     node_type=Sink,
        #     inputs={_bus_sink: Flow()},
        # )

        # self.create_solph_node(
        #     label="converter1",
        #     node_type=Converter,
        #     inputs={
        #         heat_bus_warm_sink: Flow(),
        #     },
        #     outputs={
        #         heat_bus_cold_sink: Flow(),
        #         _bus_sink: Flow(nominal_value=self.nominal_power),
        #     },
        #     conversion_factors={
        #         _bus_sink: (1 - ratio),
        #         heat_bus_cold_sink: ratio,
        #         heat_bus_warm_sink: 1,
        #     },
        # )
