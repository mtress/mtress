from dataclasses import dataclass


@dataclass
class IceStorage:
    volume: float = 100  # m³
    height: float = 3  # m
    wall_thickness: float = 0.1  # m
    ceil_thickness: float = 0.2  # m
