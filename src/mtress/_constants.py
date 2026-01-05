from enum import IntEnum


class EnergyType(IntEnum):
    UNDEFINED = 0
    ELECTRICITY = 1
    HEAT = 2
    GAS = 3


ELECTRICITY_COLOR = "orange"
GAS_COLOR = "steelblue"
HEAT_COLOR = "maroon"
