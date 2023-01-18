"""Energy demands."""

from ._electricity import Electricity
from ._fixed_temperature_heat import FixedTemperatureHeat

__all__ = [
    "Electricity",
    "FixedTemperatureHeat",
]
