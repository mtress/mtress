"""This module provides a class representing an air heat exchanger."""

from oemof.solph import Bus, Flow
from oemof.solph.components import Source, Converter, Sink

from .._abstract_component import AbstractSolphRepresentation
from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ._abstract_technology import AbstractTechnology, AbstractAnergySource
from ..carriers import HeatCarrier


class AirHeatExchanger(AbstractTechnology, AbstractSolphRepresentation):
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
        air_temperatures: float,
        # flow_temperature: float = None,
        minimum_temperature: float = 0,
        nominal_power: float = None,
        source: bool = True,
    ):
        """
        Initialize air heat exchanger for e.g. heat pumps.

        :param name: Name of the component.
        :param nominal_power: Nominal power of the heat exchanger (in W), default to None.
        :param air_temperatures: Reference to air temperature time series
        """
        super().__init__(name=name)

        self.air_temperatures = air_temperatures
        self.nominal_power = nominal_power
        # self.flow_temperature = flow_temperature
        self.minimum_temperature = minimum_temperature
        self.source = source

        # Solph model interfaces
        self._bus_source = None
        self._bus_sink = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        # self.air_temperatures = self._solph_model.data.get_timeseries(
        #     self.air_temperatures,
        #     kind=TimeseriesType.INTERVAL,
        # )

        heat_carrier = self.location.get_carrier(HeatCarrier)

        warm_level_heating, _ = heat_carrier.get_surrounding_levels(
            self.air_temperatures
        )
        _, cold_level_heating = heat_carrier.get_surrounding_levels(
            self.minimum_temperature
        )

        reference_temp = heat_carrier.reference

        ratio = (cold_level_heating - reference_temp) / (
            warm_level_heating - reference_temp
        )

        heat_bus_cold = heat_carrier.level_nodes[cold_level_heating]
        heat_bus_warm = heat_carrier.level_nodes[warm_level_heating]

        if self.source == True:
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
                    heat_bus_cold: Flow(),
                },
                outputs={heat_bus_warm: Flow()},
                conversion_factors={
                    _bus_source: (1 - ratio),
                    heat_bus_cold: ratio,
                    heat_bus_warm: 1,
                },
            )

        else:
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
                label="converter",
                node_type=Converter,
                inputs={
                    heat_bus_warm: Flow(),
                },
                outputs={
                    _bus_sink: Flow(nominal_value=self.nominal_power),
                    heat_bus_cold: Flow(),
                },
                conversion_factors={
                    heat_bus_cold: ratio,
                    heat_bus_warm: (1 - ratio),
                    _bus_sink: 1,
                },
            )

    # @property
    # def temperature(self):
    #     """Return temperature level of the air."""
    #     return self.air_temperatures

    # @property
    # def bus_source(self):
    #     """Return _bus to connect to."""
    #     return self._bus_source
