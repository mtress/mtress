import sys

import time
import pandas as pd
import matplotlib.pyplot as plt

from oemof.solph import views, processing

from meta_model.enaq_meta_model import ENaQMetaModel
from meta_model.physics import celsius_to_kelvin


def extract_result_sequence(results, label, resample=None):
    """
    :param results:
    :param label:
    :param resample: resampling frequency identifier (e.g. 'D')
    :return:
    """
    sequences = views.node(results, label)['sequences']
    if resample is not None:
        sequences = sequences.resample(resample).mean()
    return sequences


def main():
    meteo = pd.read_csv('meteo.csv',
                        comment='#', index_col=0,
                        sep=',',
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
    variables = {
        'meteorology': {
            'temp_air': meteo['temp_air'],  # K (timeseries)
            'temp_soil': meteo['temp_soil']},  # K (timeseries)
            'temperatures': {
                'reference': celsius_to_kelvin(0),  # K
                'dhw': celsius_to_kelvin(60),  # K
                'heat_drop_exchanger_dhw': 5,  # K
                'heating': celsius_to_kelvin(40),  # K
                'heat_drop_heating': 10,
                'intermediate': [celsius_to_kelvin(20),  # K
                                 celsius_to_kelvin(30)]},  # K
        'heat_pump': {
            'electric_input': 0.100},  # MW
        'near_surface_heat_source': {
            'thermal_output': 0},  # MW
        'geothermal_heat_source': {
            'thermal_output': 0,  # MW
            'temperature': 15},
        'ice_storage': {
            'volume': 100,  # m³
            'height': 3,  # m
            'wall_thickness': 0.1,  # m
            'ceil_thickness': 0.2},  # m
        'thermal_ground_storage': {
            'volume': 100,  # m³
            'temperature': celsius_to_kelvin(10),  # K
            'heat_capacity': 0.025},  # MWh/m³
        'gas_boiler': {
            'efficiency': 0.85,
            'thermal_output': 0.100},  # MW
        'pellet_boiler': {
            'efficiency': 0.80,
            'thermal_output': 0.100},  # MW
        'chp': {
            'biomethane_fraction': 0.2,
            'feed_in_tariff_funded': day_ahead['price'] + 7.5,  # €/MWh
            'feed_in_tariff_unfunded': day_ahead['price'],  # €/MWh
            'own_consumption_tariff_funded': day_ahead['price'] + 3.5,  # €/MWh
            'funding_hours_per_year': 3500,  # h/a
            'electric_output': 0.100,  # MW
            'electric_efficiency': 0.4,
            'thermal_output': 0.150,  # MW
            'thermal_efficiency': 0.5,
            'gas_input': 0.270},  # MW
        'pv': {
            'nominal_power': 1,
            'feed_in_tariff': 75,  # €/MWh
            'generation': generation['PV']},  # MW (timeseries)
        'wind_turbine': {
            'nominal_power': 1,
            'feed_in_tariff': 75,  # €/MWh
            'generation': generation['WT']},  # MW (timeseries)
        'solar_thermal': {
            'st_area': 1,
            'generation': generation.filter(regex='ST')},  # MW (timeseries)
        'power_to_heat': {
            'thermal_output': 0.05},  # MW
        'battery': {
            'power': 50,  # MW
            'capacity': 250,  # MWh
            'efficiency_inflow': 0.98,
            'efficiency_outflow': 0.98,
            'self_discharge': 1E-6},
        'heat_storage': {
            'volume': 10,  # m³
            'diameter': 2,  # m
            'insulation_thickness': 0.10},  # m
        'energy_cost': {
            'electricity': {
                'AP': day_ahead['price'] + 17,  # €/MWh
                'LP': 15000},  # €/MW
            'fossil_gas': 35,  # €/MWh
            'biomethane': 95,  # €/MWh
            'wood_pellet': 300,  # €/MWh
            'eeg_levy': 64.123},  # €/MWh
        'demand': {
            'electricity': demand['electricity'],  # MW (time series)
            'heating': demand['heating'],  # MW (time series)
            'dhw': demand['dhw']},  # MW (time series),
        'co2': {
            'fossil_gas': 0.202,
            'biomethane': 0.148,
            'wood_pellet': 0.023,
            'el_in': 0.401,
            'el_out': -0.401,
            'price': 0}
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

    results = energy_system.results['main']
    result_sequences_heat = extract_result_sequence(
        results, 'heat_exchanger')
    result_sequences_heat.plot(drawstyle="steps-post")

    plt.show()


if __name__ == '__main__':
    main()
