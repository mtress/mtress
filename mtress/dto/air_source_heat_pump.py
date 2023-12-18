import pandas as pd
from dataclasses import dataclass


@dataclass
class AirSourceHeatPump:
    electric_input: float = 0.1 # MW
    cop_0_35: float = 3 # 1
    thermal_output_flows: pd.Series = None
    thermal_output_flows_unit: str = "MW"
    _thermal_output_flows_unit: str = "MW"  # Internally used unit by MTRESS. Should never be touched
    electricity_input_flows: pd.Series = None
    electricity_input_flows_unit: str = "MW"
    _electricity_input_flows_unit: str = "MW"  # Internally used unit by MTRESS. Should never be touched
