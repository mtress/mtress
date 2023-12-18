from dataclasses import dataclass


@dataclass
class PelletBoiler:
    efficiency: float = 0.80 # 1
    thermal_output: float = 0.100  # MW
