# -*- coding: utf-8 -*-

"""
Additions to oemof.solph._plumbing

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

from collections import UserDict

import numpy as np
from oemof.solph import _plumbing


def sequence_compare(a, b, *, function=None) -> bool:
    if function is None:
        function = np.array_equal
    if isinstance(a, _plumbing._FakeSequence):
        a = a.value
    if isinstance(b, _plumbing._FakeSequence):
        b = b.value
    return function(a, b, equal_nan=True)


def maxseq(a, b):
    """Get the element-wise maximum of two sequences"""
    if isinstance(a, _plumbing._FakeSequence):
        a = a.value
    if isinstance(b, _plumbing._FakeSequence):
        b = b.value

    return _plumbing.sequence(np.maximum(a, b))

def minseq(a, b):
    """Get the element-wise minimum of two sequences"""
    if isinstance(a, _plumbing._FakeSequence):
        a = a.value
    if isinstance(b, _plumbing._FakeSequence):
        b = b.value

    return _plumbing.sequence(np.minimum(a, b))


class TypeAccessContainer(UserDict):
    """Container that allows entry access by type down to a defined base type.
    """
    def __init__(self, deepest_parent_class):
        super().__init__(None)
        self._deepest_parent_class = deepest_parent_class

        self._all_objects = set()

    def __iter__(self):
        return iter(self._all_objects)

    def __len__(self):
        return len(self._all_objects)

    def add(self, *objects):
        for obj in objects:
            types = type(obj).__mro__
            types = types[: types.index(self._deepest_parent_class) + 1]
            for object_type in types:
                if object_type not in self:
                    self[object_type] = set()
                self._all_objects.add(obj)
                self[object_type].add(obj)
