from dataclasses import dataclass
import pandas as pd


@dataclass
class Meteorology:
    temp_air: pd.DataFrame = None
    temp_soil: pd.DataFrame = None
    trigger_dummy: str = None # This dummy exists to prevent the event-based simulator to trigger when new data will send without reschedule reason
