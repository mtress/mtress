# -*- coding: utf-8 -*-

"""
Additions to oemof.solph._plumbing

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""


import numpy as np
from oemof.solph import _plumbing

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
