# -*- coding: utf-8 -*-
import time
import pandas as pd
import json
import os

from oemof.solph import views, processing

from mtress.meta_model import MetaModel


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


def all_techs_model(number_of_time_steps=365 * 24,
                    silent=False):
    """
    :param number_of_time_steps: number of time steps to consider
    :param silent: just solve and do not print results (for testing/ debug)
    """
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

    data = meteo.join(day_ahead)
    data = data.join(demand)
    data = data.join(generation)

    del day_ahead
    del demand
    del generation

    data = data.dropna()
    data = data.resample("1h").mean()

    data = data.head(number_of_time_steps)

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

    if not silent:
        print('\n')
        print('KPIs')
        print("OPEX: {:.2f} €".format(meta_model.operational_costs()))
        print("CO2 Emission: {:.0f} t".format(meta_model.co2_emission().sum()))
        print("Own Consumption: {:.1f} %".format(meta_model.own_consumption() * 100))
        print("Self Sufficiency: {:.1f} %".format(meta_model.self_sufficiency() * 100))

        heat_demand = meta_model.aggregate_flows(meta_model.demand_th_flows).sum()

        print('\n')
        print("Heat demand: {:6.3f}".format(heat_demand))
        print("    missing: {:6.3f}".format(
            meta_model.aggregate_flows(meta_model.missing_heat_flow).sum()))

        hs_in = meta_model._thermal_storage.combined_inflow.sum()
        hs_out = meta_model._thermal_storage.combined_outflow.sum()
        print("Storage out: {:6.3f}".format(hs_out))
        print("         in: {:6.3f}".format(hs_in))
        losses = hs_in - hs_out
        print("{:04.1f} % loss: {:6.3f}".format(100 * losses / heat_demand,
                                                losses))

        print("")
        gt_generation = meta_model.aggregate_flows(meta_model.geothermal_input_flows).sum()
        print("{:04.1f} % geothermal coverage: {:.3f}".format(
            100 * gt_generation / heat_demand, gt_generation))
        bhp_generation = meta_model.aggregate_flows(meta_model.bhp_th_flows).sum()
        print("{:04.1f} % heat pump coverage: {:.3f}".format(
            100 * bhp_generation / heat_demand, bhp_generation))
        st_generation = meta_model.aggregate_flows(meta_model.solar_thermal_th_flows).sum()
        print("{:04.1f} % solar coverage: {:.3f}".format(
            100 * st_generation / heat_demand, st_generation))
        chp_th_generation = meta_model.aggregate_flows(meta_model.chp_th_flows).sum()
        print("{:04.1f} % CHP coverage: {:.3f}".format(
            100 * chp_th_generation / heat_demand, chp_th_generation))
        pellet_generation = meta_model.aggregate_flows(meta_model.pellet_th_flows).sum()
        print("{:04.1f} % pellet coverage: {:.3f}".format(
            100 * pellet_generation / heat_demand, pellet_generation))
        boiler_generation = meta_model.aggregate_flows(meta_model.boiler_th_flows).sum()
        print("{:04.1f} % boiler coverage: {:.3f}".format(
            100 * boiler_generation / heat_demand, boiler_generation))
        p2h_generation = meta_model.aggregate_flows(meta_model.p2h_th_flows).sum()
        print("{:04.1f} % power2heat coverage: {:.3f}".format(
            100 * p2h_generation / heat_demand, p2h_generation))

        el_demand = meta_model.aggregate_flows(meta_model.demand_el_flows).sum()

        print('\n')
        print("Electricity demand: {:.3f}".format(el_demand))

        pv_generation = meta_model.aggregate_flows(meta_model.pv_el_flows).sum()
        print("{:04.1f} % PV coverage: {:.3f}".format(
            100 *pv_generation / el_demand, pv_generation))
        chp_el_generation = meta_model.aggregate_flows(meta_model.chp_el_flows).sum()
        print("{:04.1f} % CHP coverage: {:.3f}".format(
            100 * chp_el_generation / el_demand, chp_el_generation))
        wt_generation = meta_model.aggregate_flows(meta_model.wt_el_flows).sum()
        print("{:04.1f} % WT coverage: {:.3f}".format(
            100 * wt_generation / el_demand, wt_generation))

    return meta_model


if __name__ == '__main__':
    all_techs_model(number_of_time_steps=7 * 24)
