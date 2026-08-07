"""Carriers to automatically connect Technologies."""

from .electricity._electricity_carrier import ElectricityCarrier
from .heat._heat_carrier import HeatCarrier

__all__ = [
    "ElectricityCarrier",
    "HeatCarrier",
]
