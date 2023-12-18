"""These data transfer objects (DTO) can be used to define the meta model. All classes are annotated as dataclasses and therefore have the to_dict method.
Using the to_dict method on the ModelVariables class can be used to pass it to the MetaModel class to instantiate it.
For example:

meteo = Meteorology()
...
model_variables = ModelVariables(meteo, ...)

meta_model = MetaModel(**model_variables.to_dict())

The models itself have all fields, which can be used in the MetaModel and are commented with the corresponding units.
"""
from .meteorology import Meteorology
from .chp import Chp
from .pv import PV
from .wind_turbine import WindTurbine
from .solar_thermal import SolarThermal
from .electricity import Electricity
from .energy_cost import EnergyCost
from .demand import Demand
from .co2 import Co2
from .temperature import Temperatures
from .heat_pump import HeatPump
from .near_surface_heat_source import NearSurfaceHeatSource
from .geothermal_heat_source import GeothermalHeatSource
from .ice_storage import IceStorage
from .thermal_ground_storage import ThermalGroundStorage
from .gas_boiler import GasBoiler
from .pellet_boiler import PelletBoiler
from .power_to_heat import PowerToHeat
from .battery import Battery
from .heat_storage import HeatStorage
from .air_source_heat_pump import AirSourceHeatPump
from .gas import Gas
from .model_variables import ModelVariables
from .scheduler import Scheduler