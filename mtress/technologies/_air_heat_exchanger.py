"""This module provides a class representing an air heat exchanger."""

from numbers import Number
from collections.abc import Sequence
from oemof import solph

from .._helpers._array_cast import numeric_array
from ._abstract_technology import AbstractAnergySource, AbstractTechnology


class AirHeatExchanger(AbstractTechnology, AbstractAnergySource):
    """
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
            air_temperatures: Sequence[Number],
            nominal_power: float = None,
            **kwargs
    ):
        """
        Initialize air heat exchanger for e.g. heat pumps.

        :param nominal_power: Nominal power of the heat exchanger.
        :param air_temperatures: Reference to air temperature time series
        """
        super().__init__(**kwargs, name=__class__)

        self._nominal_power = nominal_power

        self._air_temperatures = numeric_array(air_temperatures)

        self._bus = None

    def build(self):
        self._bus = bus = solph.Bus(
            label=self._generate_label("output"),
        )

        source = solph.Source(
            label=self._generate_label("source"),
            outputs={bus: solph.Flow(nominal_value=self._nominal_power)},
        )

        self.location.energy_system.add(source, bus)

    @property
    def temperature(self):
        """Return temperature level of anergy source."""
        return self._air_temperatures

    @property
    def bus(self):
        """Return output bus."""
        return self._bus
