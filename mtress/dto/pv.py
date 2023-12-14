from dataclasses import dataclass, InitVar
import pandas as pd


@dataclass
class PV:
    spec_generation: pd.DataFrame = None  # data['PV']},  # MW (timeseries)
    spec_generation_unit: str = "MW"
    _spec_generation_unit: str = "MW"  # Internally used unit by MTRESS. Should never be touched
    nominal_power: float = 1
    feed_in_subsidy: float = 75  # €/MWh
    database: InitVar[pd.DataFrame] = None
    electricity_output: pd.Series = None
    electricity_output_unit: str = "MW"
    _electricity_output_unit: str = "MW"  # Internally used unit by MTRESS. Should never be touched

    def __post_init__(self, database: pd.DataFrame):
        if database is not None:
            df = database["pv"]
            if df is not None:
                df[df < 0] = 0 # PV should never be under 0 for the model to work
                self.spec_generation = df
