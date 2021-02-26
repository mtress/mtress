# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: KEHAG Energiehandel GMbH
SPDX-FileCopyrightText: Lucas Schmeling
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""
import time
from datetime import datetime

from example import all_techs_model


def test_example():
    return all_techs_model(number_of_time_steps=3,
                           silent=True)


if __name__ == "__main__":
    timestamp = datetime.fromtimestamp(time.time())
    timestamp = timestamp.isoformat()
    meta_model = test_example()
    meta_model.model.write("all_techs_example" + timestamp + ".lp",
                           io_options={'symbolic_solver_labels': True})
