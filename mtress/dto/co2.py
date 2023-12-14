from dataclasses import dataclass
import pandas as pd


@dataclass
class Co2:
    el_in: float = 0.427  # data['spec_co2 (t/MWh)'],  # t/MWh
    el_out: float = 0.427 # -data['spec_co2 (t/MWh)'],  # t/MWh
    fossil_gas: float = 0.202  # t/MWh
    biomethane: float = 0.148  # t/MWh
    wood_pellet: float = 0.023  # t/MWh
    price_el: float = 0  # €/t
    price_gas: float = 0  # €/t