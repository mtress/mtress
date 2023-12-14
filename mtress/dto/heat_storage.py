import pandas as pd
from dataclasses import dataclass, field


@dataclass
class HeatStorage:
    _initial_storage_levels: dict[int, float] = field(default_factory=lambda: {40: 0.0}) # sum of the following needs to be <= 1
    volume: float = 10  # m³
    diameter: float = 2  # m
    insulation_thickness: float = 0.10  # m
    max_heat = 40

    initial_storage_levels_unit: str = ''
    _initial_storage_levels_unit: str = ''
    thermal_input_flows: pd.Series = None
    thermal_input_flows_unit: str = "MW"
    _thermal_input_flows_unit: str = "MW" # Internally used unit by MTRESS. Should never be touched
    thermal_output_flows: pd.Series = None
    thermal_output_flows_unit: str = "MW"
    _thermal_output_flows_unit: str = "MW" # Internally used unit by MTRESS. Should never be touched
    content: pd.Series = None
    content_unit: str = ""
    _content_unit: str = "MWh"

    @property
    def initial_storage_levels(self):
        return self._initial_storage_levels

    @initial_storage_levels.setter
    def initial_storage_levels(self, value):
        if not isinstance(value, dict):
            value = {self.max_heat: value}
        self._initial_storage_levels = value

