#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script for using MTRESS using (only) the JSON interface

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

import yaml
import os
import pandas as pd
import sys

from mtress import MetaModel


def _read_csv_files(parameter_dict, dir_path, time_range):
    for key in parameter_dict:
        item = parameter_dict[key]
        if isinstance(item, dict):
            _read_csv_files(parameter_dict[key], dir_path, time_range)
        elif isinstance(item, str) and ".csv:" in item:
            file_name, column_name = item.split(":", 1)
            csv_data = pd.read_csv(os.path.join(dir_path, file_name),
                                   comment='#', index_col=0,
                                   sep=',',
                                   parse_dates=True)
            last_step = min(time_range[1], len(csv_data))
            csv_data = csv_data.iloc[time_range[0]:time_range[1]]
            parameter_dict[key] = csv_data[column_name]


def run_mtress(parameters,
               time_range=(0, -1),
               solver="cbc"):
    """
    :param parameters: dict or file name of yaml file holding configuration
    :param time_range: tuple (first time step, last time step)
    :param solver: solver to use for oemof.solph
    """
    if isinstance(parameters, dict):
        dir_path = parameters["dir_path"]
        del parameters["dir_path"]
    else:
        if isinstance(parameters, str):
            dir_path = os.path.dirname(os.path.realpath(parameters))
            with open(parameters) as file:
                parameters = yaml.safe_load(file)

    _read_csv_files(parameters, dir_path, time_range=time_range)

    meta_model = MetaModel(**parameters)
    meta_model.solve(solver=solver,
                     solve_kwargs={'tee': False},
                     cmdline_options={'ratio': 0.01})

    return meta_model


if __name__ == '__main__':
    script_path = os.path.realpath(__file__)
    if len(sys.argv) < 2:
        script_dir = os.path.dirname(script_path)
        yaml_file_name = os.path.join(script_dir,
                                      "../example/all_techs_example.yaml")
    else:
        path = sys.argv[1]
        if os.path.exists(path):
            yaml_file_name = path
        else:
            print("Usage:", script_path, "config.yaml")
            sys.exit()
    run_mtress(parameters=yaml_file_name)
