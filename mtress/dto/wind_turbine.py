from dataclasses import dataclass, InitVar
import pandas as pd


@dataclass
class WindTurbine:
    spec_generation: pd.DataFrame  # data['WT']},  # MW (timeseries)
    nominal_power: float = 1
    feed_in_tariff: float = 75  # €/MWh
    database: InitVar[pd.DataFrame] = None

    def __post_init__(self, database: pd.DataFrame):
        df = database["wind_tourbine"]
        if df is not None:
            self.spec_generation = df
