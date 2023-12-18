# This class shall represent the variables that are put into the model, i.e. meteorology time series,
# heat_pump information, etc. It shall be able to convert the information into a python dict, so that it can be fed
# into the ENaQ model

from dataclasses import dataclass, asdict, field

from . import Meteorology, Chp, PV, WindTurbine, SolarThermal, EnergyCost, Demand, Co2,\
    Temperatures, HeatPump, NearSurfaceHeatSource, GeothermalHeatSource, IceStorage,\
    ThermalGroundStorage, GasBoiler, PelletBoiler, PowerToHeat, Battery, HeatStorage, AirSourceHeatPump


@dataclass
class ModelVariables:
    meteorology: Meteorology
    energy_cost: EnergyCost
    demand: Demand
    co2: Co2

    # For testing purposes, these dataclasses do not need initialization, this will surely change later
    chp: Chp = field(default=None)
    pv: PV = field(default=None)
    wind_turbine: WindTurbine = field(default=None)
    solar_thermal: SolarThermal = field(default=None)
    temperatures: Temperatures = Temperatures()
    heat_pump: HeatPump = field(default=None)
    near_surface_heat_source: NearSurfaceHeatSource = field(default=None)
    geothermal_heat_source: GeothermalHeatSource = field(default=None)
    ice_storage: IceStorage = field(default=None)
    thermal_ground_storage: ThermalGroundStorage = field(default=None)
    gas_boiler: GasBoiler = field(default=None)
    pellet_boiler: PelletBoiler = field(default=None)
    power_to_heat: PowerToHeat = field(default=None)
    battery: Battery = field(default=None)
    heat_storage: HeatStorage = field(default=None)
    air_source_heat_pump: AirSourceHeatPump = field(default=None)
    allow_missing_heat: bool = True
    exclusive_grid_connection: bool = True

    def to_dict(self) -> dict:
        return asdict(self)
