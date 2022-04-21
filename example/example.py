# -*- coding: utf-8 -*-

"""
Example showing usage of MTRESS

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""

import os

from oemof.solph import views

from mtress.run_mtress import run_mtress


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


def all_techs_model(first_time_step=0,
                    last_time_step=-1,
                    silent=False):
    """
    :param first_time_step: first time step to consider (int)
    :param last_time_step: last time step to consider (int)
    :param silent: just solve and do not print results (for testing/ debug)
    """

    # define input data source
    dir_path = os.path.dirname(os.path.realpath(__file__))
    yaml_file_name = os.path.join(dir_path,
                                  "all_techs_example.yaml")

    # run model using input data as defined in that file
    meta_model = run_mtress(parameters=yaml_file_name,
                            time_range=(first_time_step, last_time_step))

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

        print("\n")
        total_electricity_generation = pv_generation + wt_generation + chp_el_generation
        if total_electricity_generation > el_demand:
            renewable_share_el = 100 * (pv_generation + wt_generation) / total_electricity_generation
        else:
            renewable_share_el = 100 * (pv_generation + wt_generation) / el_demand
        print("{:04.1f} % Renewable share of electricity: {:.3f}".format(
            renewable_share_el, pv_generation + wt_generation))

    return meta_model


if __name__ == '__main__':
    all_techs_model(last_time_step=7 * 24)
