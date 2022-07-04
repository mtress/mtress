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

from mtress import (
    prepare_mtress_config,
    MetaModel,
)


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
    config = prepare_mtress_config(
        parameters=yaml_file_name,
        time_range=(first_time_step, last_time_step)
    )
    config["save_config"] = os.path.join(
        dir_path,
        "all_techs_example-copy.yaml"
    )

    meta_model = MetaModel(**config)


if __name__ == '__main__':
    all_techs_model(last_time_step=7 * 24)
