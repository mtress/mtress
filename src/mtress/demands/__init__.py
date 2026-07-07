"""Energy demands."""

from ._electricity import Electricity
from ._heat_exchanger._fixed_return_temperature import (
    FixedReturnCooling,
    FixedReturnHeating,
)
from ._heat_exchanger._incremental_temperature import (
    SteppedReturnHeating,
)
from ._gas import GasDemand

__all__ = [
    "Electricity",
    "FixedTemperatureCooling",
    "FixedTemperatureHeating",
    "GasDemand",
    "SteppedReturnHeating"
]
