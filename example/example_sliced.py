# -*- coding: utf-8 -*-
import time
import pandas as pd
import json
import os

from oemof.solph import views, processing

from mtress.meta_model import MetaModel


def all_techs_model(number_of_time_steps=365 * 24,
                    slices=12,
                    silent=False):
    """
    :param number_of_time_steps: number of time steps to consider
    :param slices: number of time slices
    :param silent: just solve and do not print results (for testing/ debug)
    """
    start_global = time.time()
    solver_time = 0
    dir_path = os.path.dirname(os.path.realpath(__file__))

    with open(os.path.join(dir_path, 'all_techs_example.json')) as f:
        variables = json.load(f)

    meteo = pd.read_csv(os.path.join(dir_path, 'meteo.csv'),
                        comment='#', index_col=0,
                        sep=',',
                        parse_dates=True)

    day_ahead = pd.read_csv(os.path.join(dir_path, 'day-ahead.csv'),
                            comment='#', index_col=0,
                            sep=',',
                            parse_dates=True)

    demand = pd.read_csv(os.path.join(dir_path, 'demand.csv'),
                         comment='#', index_col=0,
                         sep=',',
                         parse_dates=True)

    generation = pd.read_csv(os.path.join(dir_path, 'generation.csv'),
                             comment='#', index_col=0,
                             sep=',',
                             parse_dates=True)

    data_global = meteo.join(day_ahead)
    data_global = data_global.join(demand)
    data_global = data_global.join(generation)

    del day_ahead
    del demand
    del generation

    data_global = data_global.dropna()
    data_global = data_global.resample("1h").mean()

    operational_costs = 0
    co2_emission = 0
    own_consumption = 0
    self_sufficiency = 0

    for i in range(1, slices+1):
        data = data_global.copy()
        data = data.head(i*number_of_time_steps//slices)
        data = data.tail(number_of_time_steps//slices)

        if not silent:
            print("Slice start:", data.index[0])

        time_series = {
            'meteorology': {
                'temp_air': meteo['temp_air'],  # K
                'temp_soil': meteo['temp_soil']},  # K
            'energy_cost': {
                'electricity': {'market': data['price']}},  # €/MW
            'demand': {
                'electricity': data['electricity'],  # MW (time series)
                'heating': data['heating'],  # MW (time series)
                'dhw': data['dhw']}  # MW (time series),
        }

        # Only add timeseries if technology is present in model
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

        variables["exclusive_grid_connection"] = True
        variables["allow_missing_heat"] = False
        meta_model = MetaModel(**variables)

        if not silent:
            print('Start solving')
        start = time.time()
        meta_model.model.solve(solver="cbc",
                               solve_kwargs={'tee': False},
                               solver_io='lp',
                               cmdline_options={'ratio': 0.01})
        end = time.time()
        solver_time += end - start
        if not silent:
            print("Time to solve: " + str(end - start) + " Seconds")

        energy_system = meta_model.energy_system
        energy_system.results['valid'] = True
        energy_system.results['main'] = processing.results(
            meta_model.model)
        energy_system.results['main'] = views.convert_keys_to_strings(
            energy_system.results['main'])
        energy_system.results['meta'] = processing.meta_results(
            meta_model.model)

        operational_costs += meta_model.operational_costs(
            feed_in_order=[{"revenue": meta_model.chp_revenue_funded,
                            "flows": meta_model.chp_export_funded_flows},
                           {"revenue": meta_model.pv_revenue,
                            "flows": meta_model.pv_export_flows},
                           {"revenue": meta_model.wt_revenue,
                            "flows": meta_model.wt_export_flows}]
        )
        co2_emission += meta_model.co2_emission().sum()
        own_consumption += meta_model.own_consumption()/slices
        self_sufficiency += meta_model.self_sufficiency()/slices

    end_global = time.time()
    if not silent:
        print("Slices:", slices)
        print("Total runtime: {:.2f} s".format(end_global - start_global))
        print("Solver runtime: {:.2f} s".format(solver_time))
        print('KPIs')
        print("OPEX: {:.2f} €".format(operational_costs))
        print("CO2 Emission: {:.1f} t".format(co2_emission.sum()))
        print("Own Consumption: {:.1f} %".format(own_consumption * 100))
        print("Self Sufficiency: {:.1f} %".format(self_sufficiency * 100))


if __name__ == '__main__':
    all_techs_model(number_of_time_steps=10 * 24, slices=2)
