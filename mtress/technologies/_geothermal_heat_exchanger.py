"""This module provides a class representing an ground heat exchanger."""


from oemof.solph import Bus, Flow
from oemof.solph.components import Source

from .._abstract_component import AbstractSolphRepresentation
from .._data_handler import TimeseriesSpecifier
from ._abstract_technology import AbstractAnergySource, AbstractTechnology

from typing import Optional
class GeothermalHeatExchanger(
    AbstractTechnology, AbstractAnergySource, AbstractSolphRepresentation
):
    """
    Geothermal heat exchanger for e.g. heat pumps.

    Functionality: Geothermal heat exchanger for e.g. heat pumps.
                   Holds a time series of both the ground temper
                   -ature and the power limit that can be drawn
                   from the source.

    Procedure: Create a simple geothermal heat exchanger by
               doing the following:

                house_1.add(
                technologies.GeothermalHeatExchanger(
                name="ghe",  ground_temperatures=[3])
                )


    Further documentation regarding anergy found in the class
    AbstractAnergysource.

    """

    def __init__(
        self,
        name: str,
        ground_temperature: TimeseriesSpecifier = 10,
        nominal_power: Optional[float] = None,
    ):
        """
        Initialize geothermal heat exchanger for e.g. heat pumps.

        :param name: Name of the component.
        :param nominal_power: Nominal power of the heat exchanger.
        :param ground_temperature: Reference to ground temperature
                                   time series
        """
        super().__init__(name=name)

        self.nominal_power = nominal_power
        self.ground_temperature = ground_temperature

        # Solph model interfaces
        self._bus = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        self.ground_temperature = self._solph_model.data.get_timeseries(
            self.ground_temperature,
            kind=TimeseriesType.INTERVAL,
        )

        self._bus = _bus = self.create_solph_node(
            label="output",
            node_type=Bus,
        )

        self.create_solph_node(
            label="source",
            node_type=Source,
            outputs={_bus: Flow(nominal_value=self.nominal_power)},
        )

    @property
    def temperature(self):
        """Return temperature level of anergy source."""
        return self.ground_temperature

    @property
    def bus(self):
        """Return _bus to connect to."""
        return self._bus
