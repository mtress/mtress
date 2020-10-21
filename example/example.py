import sys

import time
import pandas as pd
from oemof.solph import views, processing

from enaq_meta_model import ENaQMetaModel
from physics import celsius_to_kelvin


def main():
    meteo = pd.read_csv('meteo.csv',
                        comment='#', index_col=0,
                        sep=';', decimal=',',
                        parse_dates=True)

    day_ahead = pd.read_csv('day-ahead.csv',
                            comment='#', index_col=0,
                            sep=',',
                        parse_dates=True)

    demand = pd.read_csv('demand.csv',
                         comment='#', index_col=0,
                         sep=',',
                         parse_dates=True)

    generation = pd.read_csv('generation.csv',
                         comment='#', index_col=0,
                         sep=',',
                        parse_dates=True)
    variables = {'meteorology':
                     {'temp_air': meteo['temp_air'],  # K (timeseries)
                      'temp_soil': meteo['temp_soil']},  # K (timeseries)
                 'temperatures':
                     {'reference': celsius_to_kelvin(0),  # K
                      'dhw': celsius_to_kelvin(60),  # K
                      'heat_drop_exchanger_dhw': 5,  # K
                      'heating': celsius_to_kelvin(40),  # K
                      'intermediate': [celsius_to_kelvin(20),  # K
                                       celsius_to_kelvin(30)]},  # K
                 'heat_pump':
                     {'electric_input': 0.100},  # MW
                 'near_surface_heat_source':
                     {'thermal_output': 0},  # MW
                 'geothermal_heat_source':
                     {'thermal_output': 0,
                      'temperature': 15},  # MW
                 'ice_storage':
                     {'volume': 100,  # m³
                      'height': 3,  # m
                      'wall_thickness': 0.1,  # m
                      'ceil_thickness': 0.2},  # m
                 'thermal_ground_storage':
                     {'volume': 100,  # m³
                      'temperature': celsius_to_kelvin(10),  # K
                      'heat_capacity': 0.025},  # MWh/m³
                 'gas_boiler':
                     {'efficiency': 0.85,
                      'thermal_output': 0.100},  # MW
                 'pellet_boiler':
                     {'efficiency': 0.80,
                      'thermal_output': 0.100},  # MW
                 'chp':
                     {'biomethane_fraction': 0.2,
                      'feed_in_tariff_funded': day_ahead['price'] + 7.5,  # €/MWh
                      'feed_in_tariff_unfunded': day_ahead['price'],  # €/MWh
                      'own_consumption_tariff_funded': day_ahead['price'] + 3.5,  # €/MWh
                      'funding_hours_per_year': 3500,  # h/a
                      'electric_output': 0.100,  # MW
                      'thermal_output': 0.150,  # MW
                      'gas_input': 0.270},  # MW
                 'pv':
                     {'feed_in_tariff': 75,  # €/MWh
                      'generation': generation['PV']},  # MW (timeseries)
                 'wind_turbine':
                     {'feed_in_tariff': 75,  # €/MWh
                      'generation': generation['WT']},  # MW (timeseries)
                 'solar_thermal':
                     {'generation': generation.filter(regex='ST')},  # MW (timeseries)
                 'power_to_heat':
                     {'thermal_output': 0.05},  # MW
                 'battery':
                     {'power': 50,  # MW
                      'capacity': 250,  # MWh
                      'efficiency_inflow': 0.98,
                      'efficiency_outflow': 0.98,
                      'self_discharge': 1E-6},
                 'heat_storage':
                     {'volume': 10,  # m³
                      'diameter': 2,  # m
                      'insulation_thickness': 0.10},  # m
                 'energy_cost':
                     {'electricity':
                         {'AP': day_ahead['price'] + 17,  # €/MWh
                          'LP': 15000},  # €/MW
                      'natural_gas': 35,  # €/MWh
                      'biomethane': 95,  # €/MWh
                      'wood_pellet': 300,  # €/MWh
                      'eeg_levy': 64.123},  # €/MWh
                 'demand':
                     {'electricity': demand['electricity'],  # MW (timeseries)
                      'heating': demand['heating'],  # MW (timeseries)
                      'dhw': demand['dhw']}  # MW (timeseries)
                 }

    meta_model = ENaQMetaModel(**variables)

    print('Start solving')
    start = time.time()
    meta_model.model.solve(solver="cbc",
                           solve_kwargs={'tee': False},
                           solver_io='lp',
                           cmdline_options={'ratio': 0.01})
    end = time.time()
    print("Time to solve: " + str(end-start) + " Seconds")

    energy_system = meta_model.energy_system
    energy_system.results['valid'] = True
    energy_system.results['main'] = processing.results(
        meta_model.model)
    energy_system.results['main'] = views.convert_keys_to_strings(
        energy_system.results['main'])
    energy_system.results['meta'] = processing.meta_results(
        meta_model.model)

    heat_demand = meta_model.thermal_demand()

    print("Heat demand", heat_demand)
    print("Geothermal coverage", meta_model.heat_geothermal()/heat_demand)
    print("Solar coverage", meta_model.heat_solar_thermal()/heat_demand)
    print("CHP coverage", meta_model.heat_chp()/heat_demand)
    print("Pellet coverage", meta_model.heat_pellet()/heat_demand)


if __name__ == '__main__':
    sys.exit(main())
