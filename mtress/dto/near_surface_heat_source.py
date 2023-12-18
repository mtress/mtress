from dataclasses import dataclass


@dataclass
class NearSurfaceHeatSource:
    thermal_output: float = 0.2  # MW
