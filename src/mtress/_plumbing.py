# -*- coding: utf-8 -*-

"""
Additions to oemof.solph._plumbing

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

from oemof.solph._plumbing import sequence

def maxseq(a, b):
    """Get the element-wise maximum of two sequences"""
    a = sequence(a)
    b = sequence(b)
    a_bigger_mask = a > b

    return sequence(
        a * a_bigger_mask + b * (1 - a_bigger_mask)
    )

def minseq(a, b):
    """Get the element-wise minimum of two sequences"""
    a = sequence(a)
    b = sequence(b)
    a_smaller_mask = a < b

    return sequence(
        a * a_smaller_mask + b * (1 - a_smaller_mask)
    )
