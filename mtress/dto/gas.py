from dataclasses import dataclass


@dataclass
class Gas:
    fossil_gas: float = 35  # €/MWh
    biomethane: float = 95  # €/MWh
    energy_tax: float = 5.5  # €/MWh
