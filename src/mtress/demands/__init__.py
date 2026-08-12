"""Demands of any energy type."""

from ._electricity._electricity_demand import ElectricityDemand
from ._heat._heat_demand import HeatDemandFixedReturn

__all__ = [
    "Electricity",
    "FixedReturnHeatDemand",
]
