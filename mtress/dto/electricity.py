from dataclasses import dataclass


@dataclass
class Electricity:
    demand_rate: float = 15000  # €/MW
    slp_price: float = 300  # €/MWh
    surcharge: float = 130  # €/MWh
    eeg_levy: float = 64.123  # €/MWh
    market: float = 30  # €/MWh
