from dataclasses import dataclass


@dataclass
class GeothermalHeatSource:
    thermal_output: float = 0.15  # MW
    temperature: float = 15 # C°
