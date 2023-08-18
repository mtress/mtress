"""Energy demands."""

from ._electricity import Electricity
from ._fixed_temperature_heat import FixedTemperatureHeat
from ._hydrogen import Hydrogen
from ._hydrogen_injection import HydrogenInjection
from ._h2_pipeline import HydrogenPipeline
from ._heat_sink import HeatSink

__all__ = [
    "Electricity",
    "FixedTemperatureHeat",
    "Hydrogen",
    "HydrogenInjection",
    "HydrogenPipeline",
    "HeatSink",
]
