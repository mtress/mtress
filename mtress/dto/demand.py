from dataclasses import dataclass
import pandas as pd


@dataclass
class Demand:
    electricity: pd.DataFrame = None # data['electricity'],  # MW (time series)
    electricity_unit: str = "MW"
    _electricity_unit: str = "MW"  # Internally used unit by MTRESS. Should never be touched
    heating: pd.DataFrame = None  # data['heating'],  # MW (time series)
    heating_unit: str = "MW"
    _heating_unit: str = "MW"  # Internally used unit by MTRESS. Should never be touched
    dhw: pd.DataFrame = None  # data['dhw']},  # MW (time series),
    dhw_unit: str = "MW"
    _dhw_unit: str = "MW"  # Internally used unit by MTRESS. Should never be touched
    trigger_dummy: str = None  # This dummy exists to prevent the event-based simulator to trigger when new data will send without reschedule reason
