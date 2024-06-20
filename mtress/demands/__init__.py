"""Energy demands."""

from ._electricity import Electricity
from ._fixed_temperature_heat import FixedTemperatureCooling
from ._fixed_temperature_heat import FixedTemperatureHeating
from ._gas import GasDemand

__all__ = [
    "Electricity",
    "FixedTemperatureCooling",
    "FixedTemperatureHeating",
    "GasDemand",
]
