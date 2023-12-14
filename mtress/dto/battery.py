import pandas as pd
from dataclasses import dataclass


@dataclass
class Battery:
    power: float = 0.125  # MW
    capacity: float = 0.250  # MWh
    efficiency_inflow: float = 0.98 # 1
    efficiency_outflow: float = 0.98 # 1
    self_discharge: float = 1E-6 # 1/h
    initial_storage_level: float = 0 # 1
    initial_storage_level_unit: str = ""
    _initial_storage_level_unit: str = ""  # Internally used unit by MTRESS. Should never be touched
    electricity_input: pd.Series = None
    electricity_input_unit: str = 'MW'
    _electricity_input_unit: str = 'MW'  # Internally used unit by MTRESS. Should never be touched
    electricity_output: pd.Series = None
    electricity_output_unit: str = 'MW'
    _electricity_output_unit: str = 'MW'  # Internally used unit by MTRESS. Should never be touched
    content: pd.Series = None
    content_unit: str = ""
    _content_unit: str = "MWh"  # Internally used unit by MTRESS. Should never be touched
    
    trigger_dummy: str = None  # This dummy exists to prevent the event-based simulator to trigger when new data will send without reschedule reason
