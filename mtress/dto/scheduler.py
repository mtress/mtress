import pandas as pd
from dataclasses import dataclass, field


@dataclass
class Scheduler:
    reschedule: int = None
    allow_missing_heat: bool = True
    exclusive_grid_connection: bool = True