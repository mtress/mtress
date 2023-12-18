from dataclasses import dataclass


@dataclass
class PowerToHeat:
    thermal_output: float = 0.05  # MW
