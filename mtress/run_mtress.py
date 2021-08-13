#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import pandas as pd

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
            csv_data = csv_data.iloc[time_range[0]:time_range[1]]
            parameter_dict[key] = csv_data[column_name]


def run_mtress(parameters,
               time_range=(0, -1),
               solver="cbc"):
    """
    :param parameters: dict or file name of json file holding configuration
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
                parameters = json.load(file)

    _read_csv_files(parameters, dir_path, time_range=time_range)

    meta_model = MetaModel(**parameters)
    meta_model.solve(solver=solver,
                     solve_kwargs={'tee': False},
                     cmdline_options={'ratio': 0.01})

    return meta_model


if __name__ == '__main__':
    script_path = os.path.dirname(os.path.realpath(__file__))
    json_file_name = os.path.join(script_path,
                                  "../example/all_techs_example.json")
    run_mtress(parameters=json_file_name)
