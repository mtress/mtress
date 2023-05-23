"""Energy demands."""

from ._electricity import Electricity
from ._fixed_temperature_heat import FixedTemperatureHeat
from ._hydrogen import Hydrogen

__all__ = [
    "Electricity",
    "FixedTemperatureHeat",
    "Hydrogen",
    "HydrogenInjection"
]
