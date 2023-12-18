from dataclasses import dataclass


@dataclass
class GasBoiler:
    efficiency: float = 0.85 # 1
    thermal_output: float = 0.100  # MW
