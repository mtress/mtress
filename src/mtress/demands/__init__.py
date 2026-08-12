"""Demands of any energy type."""

from .electricity._electricity import Electricity
from .heat._heat_demand import FixedReturnHeatDemand

__all__ = [
    "Electricity",
    "FixedReturnHeatDemand",
]
