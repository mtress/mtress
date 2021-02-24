# -*- coding: utf-8 -*-

"""
SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: KEHAG Energiehandel GMbH
SPDX-FileCopyrightText: Lucas Schmeling
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

from example import all_techs_model


def test_example():
    all_techs_model(number_of_time_steps=24,
                    silent=True)


if __name__ == "__main__":
    test_example()
