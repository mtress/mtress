"""Energy demands."""

from ._electricity import Electricity
from ._heat_exchanger._fixed_return_temperature import (
    FixedTemperatureCooling,
    FixedTemperatureHeating,
)
from ._gas import GasDemand

__all__ = [
    "Electricity",
    "FixedTemperatureCooling",
    "FixedTemperatureHeating",
    "GasDemand",
]
