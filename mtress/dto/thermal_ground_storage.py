from dataclasses import dataclass


@dataclass
class ThermalGroundStorage:
    volume: float = 100  # m³
    temperature: float = 10  # C°
    heat_capacity: float = 0.025  # MWh/m³
