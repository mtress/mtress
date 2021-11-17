# -*- coding: utf-8 -*-

"""
basic heat layer functionality

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""


class GenericTechnology:
    def __init__(self,
                 label):
        self._flows_in = dict()
        self._flows_out = dict()
        self._label = label
        self._solph_nodes = set()

    @property
    def flows_in(self):
        return self._flows_in

    @property
    def flows_out(self):
        return self._flows_out

    @property
    def solph_nodes(self):
        return self._solph_nodes
