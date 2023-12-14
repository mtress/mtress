from dataclasses import dataclass


@dataclass
class Chp:
    biomethane_fraction: float = 0.2
    funding_hours_per_year: float = 3500  # h/a
    electric_output: float = 0.100  # MW
    electric_efficiency: float = 0.4 # 1
    feed_in_subsidy: float = 75  # €/MWh
    own_consumption_subsidy: float = 35  # €/MWh
    thermal_output: float = 0.150  # MW
    thermal_efficiency: float = 0.5 # 1
    gas_input: float = 0.270  # MW
