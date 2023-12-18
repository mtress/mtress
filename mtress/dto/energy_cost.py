from dataclasses import dataclass
from .electricity import Electricity
from .gas import Gas


@dataclass
class EnergyCost:
    electricity: Electricity
    gas: Gas
    wood_pellet: float = 300  # €/MWh
