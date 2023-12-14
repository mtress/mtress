from dataclasses import dataclass, InitVar
import pandas as pd


@dataclass
class SolarThermal:
    spec_generation: pd.DataFrame  # data.filter(regex='ST')},  # MW (timeseries)
    st_area: float = 1
    database: InitVar[pd.DataFrame] = None

    def __post_init__(self, database: pd.DataFrame):
        df = database.filter(regex="solar_thermal")
        if df is not None:
            self.spec_generation = df
