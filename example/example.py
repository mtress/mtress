import time
import pandas as pd

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
            'feed_in_tariff_funded': data['price'] + 7.5,  # €/MWh
            'feed_in_tariff_unfunded': data['price'],  # €/MWh
            'own_consumption_tariff_funded': data['price'] + 3.5,  # €/MWh
            'funding_hours_per_year': 3500,  # h/a
            'electric_output': 0.100,  # MW
            'electric_efficiency': 0.4,
            'thermal_output': 0.150,  # MW
            'thermal_efficiency': 0.5,
            'gas_input': 0.270},  # MW
        'pv': {
            'nominal_power': 1,
            'feed_in_tariff': 75,  # €/MWh
            'generation': data['PV']},  # MW (timeseries)
        'wind_turbine': {
            'nominal_power': 1,
            'feed_in_tariff': 75,  # €/MWh
            'generation': data['WT']},  # MW (timeseries)
        'solar_thermal': {
            'st_area': 1,
            'generation': data.filter(regex='ST')},  # MW (timeseries)
        'power_to_heat': {
            'thermal_output': 0.05},  # MW
        'battery': {
            'power': 0.125,  # MW
            'capacity': 0.250,  # MWh
            'efficiency_inflow': 0.98,
            'efficiency_outflow': 0.98,
            'self_discharge': 1E-6},
        'heat_storage': {
            'volume': 10,  # m³
            'diameter': 2,  # m
            'insulation_thickness': 0.10},  # m
        'energy_cost': {
            'electricity': {
                'AP': data['price'] + 17,  # €/MWh
                'LP': 15000,  # €/MW
                'market': data['price']},  # €/MW
            'fossil_gas': 35,  # €/MWh
            'biomethane': 95,  # €/MWh
            'wood_pellet': 300,  # €/MWh
            'eeg_levy': 64.123},  # €/MWh
        'demand': {
            'electricity': data['electricity'],  # MW (time series)
            'heating': data['heating'],  # MW (time series)
            'dhw': data['dhw']},  # MW (time series),
        'co2': {
            'fossil_gas': 0.202,  # t/MWh
            'biomethane': 0.148,  # t/MWh
            'wood_pellet': 0.023,  # t/MWh
            'el_in': data['spec_co2 (t/MWh)'],  # t/MWh
            'el_out': -data['spec_co2 (t/MWh)'],  # t/MWh
            'price': 0}  # €/t
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

    print("Heat demand: {:.3f}".format(heat_demand))
    print("{:04.1f} % geothermal coverage".format(
        100*meta_model.heat_geothermal()/heat_demand))
    print("{:04.1f} % solar coverage".format(
        100*meta_model.heat_solar_thermal()/heat_demand))
    print("{:04.1f} % CHP coverage".format(
        100*meta_model.heat_chp()/heat_demand))
    print("{:04.1f} % pellet coverage".format(
        100*meta_model.heat_pellet()/heat_demand))
    print("{:04.1f} % boiler coverage".format(
        100*meta_model.heat_boiler()/heat_demand))
    print("{:04.1f} % power2heat coverage".format(
        100*meta_model.heat_p2h()/heat_demand))


if __name__ == '__main__':
    main()
