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
    mask_a_bigger = a > b

    return sequence(
        a * mask_a_bigger + b * (1 - mask_a_bigger)
    )

def minseq(a, b):
    """Get the element-wise minimum of two sequences"""
    mask_a_bigger = a > b

    return sequence(
        a * (1 - mask_a_bigger) + b * mask_a_bigger
    )
