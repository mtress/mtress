"""Energy demands."""

from ._heat_exchanger._fixed_return_temperature import (
    FixedReturnCooling,
    FixedReturnHeating,
)
from ._heat_exchanger._incremental_temperature import (
    SteppedReturnHeating,
)

__all__ = [
    "FixedReturnCooling",
    "FixedReturnHeating",
    "SteppedReturnHeating",
]
