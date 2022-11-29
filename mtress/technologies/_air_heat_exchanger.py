"""This module provides a class representing an air heat exchanger."""


from oemof import solph

from .._abstract_component import AbstractSolphComponent
from ._abstract_technology import AbstractAnergySource, AbstractTechnology


class AirHeatExchanger(
    AbstractTechnology, AbstractAnergySource, AbstractSolphComponent
):
    """Air heat exchanger for e.g. heat pumps."""

    def __init__(self, name: str, air_temperatures, nominal_power: float = None):
        """
        Initialize air heat exchanger for e.g. heat pumps.

        :param name: Name of the component.
        :param nominal_power: Nominal power of the heat exchanger.
        :param air_temperatures: Reference to air temperature time series
        """
        super().__init__(name)

        self.nominal_power = nominal_power
        self.air_temperatures = air_temperatures

        # Solph model interfaces
        self.bus = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        self.air_temperatures = self._solph_model.data.get_timeseries(
            self.air_temperatures
        )

        self.bus = bus = self._solph_model.add_solph_component(
            mtress_component=self,
            label="output",
            solph_component=solph.Bus,
        )

        self._solph_model.add_solph_component(
            mtress_component=self,
            label="source",
            solph_component=solph.Source,
            outputs={bus: solph.Flow(nominal_value=self.nominal_power)},
        )

    @property
    def temperature(self):
        """Return temperature level of anergy source."""
        return self.air_temperatures
