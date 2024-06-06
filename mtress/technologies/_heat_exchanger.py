"""This module provides a class representing an air heat exchanger."""

from oemof.solph import Bus, Flow
from oemof.solph.components import Source, Converter, Sink

from .._abstract_component import AbstractSolphRepresentation
from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ._abstract_technology import AbstractTechnology, AbstractAnergySource
from ..carriers import HeatCarrier


class HeatExchanger(AbstractTechnology, AbstractSolphRepresentation):
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
        minimum_temperature: float = 0,
        maximum_temperature: float = 0,
        nominal_power: float = None,
    ):
        """
        Initialize air heat exchanger for e.g. heat pumps.

        :param name: Name of the component.
        :param nominal_power: Nominal power of the heat exchanger (in W), default to None.
        :param air_temperatures: Reference to air temperature time series
        """
        super().__init__(name=name)

        self.reservoir_temperature = reservoir_temperature
        self.minimum_temperature = minimum_temperature
        self.maximum_temperature = maximum_temperature
        self.nominal_power = nominal_power

        # Solph model interfaces
        self._bus_source = None
        self._bus_sink = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        self.reservoir_temperature = self._solph_model.data.get_timeseries(
            self.reservoir_temperature,
            kind=TimeseriesType.INTERVAL,
        )

        heat_carrier = self.location.get_carrier(HeatCarrier)

        heat_bus_warm_source, heat_bus_cold_source, ratio = (
            heat_carrier.get_connection_heat_transfer(
                self.reservoir_temperature, self.minimum_temperature
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

        self.create_solph_node(
            label="converter",
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

        heat_bus_warm_sink, heat_bus_cold_sink, ratio = (
            heat_carrier.get_connection_heat_transfer(
                self.maximum_temperature, self.reservoir_temperature
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

        self.create_solph_node(
            label="converter1",
            node_type=Converter,
            inputs={
                heat_bus_warm_sink: Flow(),
            },
            outputs={
                heat_bus_cold_sink: Flow(),
                _bus_sink: Flow(nominal_value=self.nominal_power),
            },
            conversion_factors={
                _bus_sink: (1 - ratio),
                heat_bus_cold_sink: ratio,
                heat_bus_warm_sink: 1,
            },
        )
