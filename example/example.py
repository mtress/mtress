import time
import pandas as pd
import json

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

    variables = {
        'meteorology': {
            'temp_air': meteo['temp_air'],  # K (timeseries)
            'temp_soil': meteo['temp_soil']},  # K (timeseries)
        'chp': {
            'feed_in_tariff_funded': data['price'] + 7.5,  # €/MWh
            'feed_in_tariff_unfunded': data['price'],  # €/MWh
            'own_consumption_tariff_funded': data['price'] + 3.5},  # €/MWh
        'pv': {
            'generation': data['PV']},  # MW (timeseries)
        'wind_turbine': {
            'generation': data['WT']},  # MW (timeseries)
        'solar_thermal': {
            'generation': data.filter(regex='ST')},  # MW (timeseries)
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

    with open('variables.json') as f:
        variables_json = json.load(f)

    for key in variables:
        inputted = []
        if key in variables_json:
            for key_2 in variables_json[key]:
                if type(variables_json[key][key_2]) == dict:
                    for key_3 in variables_json[key][key_2]:
                        variables[key][key_2][key_3] = variables_json[key][key_2][key_3]
                else:
                    variables[key][key_2] = variables_json[key][key_2]
                    inputted.append(key)
    for key in variables_json:
        if not key in variables:
            variables[key] = variables_json[key]

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

    heat_demand = meta_model.thermal_demand()

    print("Heat demand: {:.3f}".format(heat_demand))
    print("{:04.1f} % geothermal coverage".format(
        100 * meta_model.heat_geothermal() / heat_demand))
    print("{:04.1f} % solar coverage".format(
        100 * meta_model.heat_solar_thermal() / heat_demand))
    print("{:04.1f} % CHP coverage".format(
        100 * meta_model.heat_chp() / heat_demand))
    print("{:04.1f} % pellet coverage".format(
        100 * meta_model.heat_pellet() / heat_demand))
    print("{:04.1f} % boiler coverage".format(
        100 * meta_model.heat_boiler() / heat_demand))
    print("{:04.1f} % power2heat coverage".format(
        100 * meta_model.heat_p2h() / heat_demand))


if __name__ == '__main__':
    main()
