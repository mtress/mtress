# -*- coding: utf-8 -*-
import time
import pandas as pd
import json

from oemof.solph import views, processing

from meta_model.enaq_meta_model import ENaQMetaModel


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


def example(number_of_time_steps=365*24):
    with open('variables.json') as f:
        variables = json.load(f)

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

    spec_co2 = pd.read_csv('spec_co2_de.csv',
                           comment='#', index_col=0,
                           sep=',',
                           parse_dates=True)

    data = meteo.join(day_ahead)
    data = data.join(demand)
    data = data.join(generation)
    data = data.join(spec_co2)

    del day_ahead
    del demand
    del generation
    del spec_co2

    data = data.dropna()
    data = data.resample("1h").mean()

    data = data.head(number_of_time_steps)

    time_series = {
        'meteorology': {
            'temp_air': meteo['temp_air'],  # K
            'temp_soil': meteo['temp_soil']},  # K
        'energy_cost': {
            'electricity': {
                'AP': data['price'] + 17,  # €/MWh
                'market': data['price']}},  # €/MW
        'demand': {
            'electricity': data['electricity'],  # MW (time series)
            'heating': data['heating'],  # MW (time series)
            'dhw': data['dhw']},  # MW (time series),
        'co2': {
            'el_in': data['spec_co2 (t/MWh)'],  # t/MWh
            'el_out': -data['spec_co2 (t/MWh)']}  # t/MWh
    }

    # Only add timeseries if technology is present in model
    if 'chp' in variables.keys():
        time_series['chp'] = {'feed_in_tariff_funded': data['price'] + 7.5,  # €/MWh
                              'feed_in_tariff_unfunded': data['price'],  # €/MWh
                              'own_consumption_tariff_funded': 3.5}  # €/MWh

    if 'pv' in variables.keys():
        time_series['pv'] = {'spec_generation': data['PV']}  # MW

    if 'wind_turbine' in variables.keys():
        time_series['wind_turbine'] = {'spec_generation': data['WT']}  # MW

    if 'solar_thermal' in variables.keys():
        time_series['solar_thermal'] = {'spec_generation': data.filter(regex='ST')}  # MW/m^2

    for key1 in time_series:
        if key1 not in variables:
            variables[key1] = time_series[key1]
        else:
            for key2 in time_series[key1]:
                if type(time_series[key1][key2]) == dict:
                    for key3 in time_series[key1][key2]:
                        variables[key1][key2][key3] = time_series[key1][key2][key3]
                else:
                    variables[key1][key2] = time_series[key1][key2]

    meta_model = ENaQMetaModel(**variables)

    print('Start solving')
    start = time.time()
    meta_model.model.solve(solver="cbc",
                           solve_kwargs={'tee': False},
                           solver_io='lp',
                           cmdline_options={'ratio': 0.01})
    end = time.time()
    print("Time to solve: " + str(end - start) + " Seconds")

    energy_system = meta_model.energy_system
    energy_system.results['valid'] = True
    energy_system.results['main'] = processing.results(
        meta_model.model)
    energy_system.results['main'] = views.convert_keys_to_strings(
        energy_system.results['main'])
    energy_system.results['meta'] = processing.meta_results(
        meta_model.model)

    heat_demand = meta_model.thermal_demand().sum()

    print('\n')
    print("Heat demand: {:.3f}".format(heat_demand))
    print("{:04.1f} % geothermal coverage: {:.3f}".format(
        100 * meta_model.heat_geothermal().sum() / heat_demand,
        meta_model.heat_geothermal().sum()))
    print("{:04.1f} % heat pump coverage: {:.3f}".format(
        100 * meta_model.heat_heat_pump().sum() / heat_demand,
        meta_model.heat_heat_pump().sum()))
    print("{:04.1f} % solar coverage: {:.3f}".format(
        100 * meta_model.heat_solar_thermal().sum() / heat_demand,
        meta_model.heat_solar_thermal().sum()))
    print("{:04.1f} % CHP coverage: {:.3f}".format(
        100 * meta_model.heat_chp().sum() / heat_demand,
        meta_model.heat_chp().sum()))
    print("{:04.1f} % pellet coverage: {:.3f}".format(
        100 * meta_model.heat_pellet().sum() / heat_demand,
        meta_model.heat_pellet().sum()))
    print("{:04.1f} % boiler coverage: {:.3f}".format(
        100 * meta_model.heat_boiler().sum() / heat_demand,
        meta_model.heat_boiler().sum()))
    print("{:04.1f} % power2heat coverage: {:.3f}".format(
        100 * meta_model.heat_p2h().sum() / heat_demand,
        meta_model.heat_p2h().sum()))

    el_demand = meta_model.el_demand().sum()

    print('\n')
    print("Electricity demand: {:.3f}".format(el_demand))
    print("{:04.1f} % PV coverage: {:.3f}".format(
        100 * meta_model.el_pv().sum() / el_demand,
        meta_model.el_pv().sum()))
    print("{:04.1f} % CHP coverage: {:.3f}".format(
        100 * meta_model.el_chp().sum() / el_demand,
        meta_model.el_chp().sum()))
    print("{:04.1f} % WT coverage: {:.3f}".format(
        100 * meta_model.el_wt().sum() / el_demand,
        meta_model.el_wt().sum()))


if __name__ == '__main__':
    example(number_of_time_steps=7*24)
