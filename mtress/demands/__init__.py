"""Energy demands."""

from ._electricity import Electricity
from ._abstract_fixed_temperature import AbstractFixedTemperature
from ._fixed_temperature_heating import FixedTemperatureHeating
from ._fixed_temperature_cooling import FixedTemperatureCooling
from ._heat_sink import HeatSink
from ._gas import GasDemand

__all__ = [
    "Electricity",
    "AbstractFixedTemperature",
    "FixedTemperatureHeating",
    "FixedTemperatureCooling",
    "GasDemand",
    "HeatSink",
]
