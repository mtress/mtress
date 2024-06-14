"""Energy demands."""

from ._electricity import Electricity
from ._fixed_temperature_heat import FixedTemperatureHeating, FixedTemperatureCooling
from ._fixed_temperature_heat import FixedTemperatureHeating
from ._heat_sink import HeatSink
from ._gas import GasDemand

__all__ = [
    "Electricity",
    "FixedTemperatureHeating",
    "FixedTemperatureCooling",
    "GasDemand",
    "HeatSink",
]
