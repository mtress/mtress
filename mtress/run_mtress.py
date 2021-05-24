#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import pandas as pd

from mtress import MetaModel


def _read_csv_files(parameter_dict, dir_path):
    for key in parameter_dict:
        item = parameter_dict[key]
        if type(item) == dict:
            _read_csv_files(parameter_dict[key], dir_path)
        elif type(item) == str and ".csv:" in item:
            file_name, column_name = item.split(":", 1)
            csv_data = pd.read_csv(os.path.join(dir_path, file_name),
                                   comment='#', index_col=0,
                                   sep=',',
                                   parse_dates=True)
            parameter_dict[key] = csv_data[column_name]


def run_mtress(json_file,
               solver="cbc"):
    """
    :param json_file: json file holding configuration
    :param solver: solver to use for oemof.solph
    """
    with open(json_file) as f:
        parameters = json.load(f)

    dir_path = os.path.dirname(os.path.realpath(json_file))

    _read_csv_files(parameters, dir_path)

    meta_model = MetaModel(**parameters)
    meta_model.model.solve(solver=solver,
                           solve_kwargs={'tee': False},
                           solver_io='lp',
                           cmdline_options={'ratio': 0.01})

    return meta_model


if __name__ == '__main__':
    script_path = os.path.dirname(os.path.realpath(__file__))
    json_file_name = os.path.join(script_path,
                                  "../example/all_techs_example.json")
    run_mtress(json_file=json_file_name)
