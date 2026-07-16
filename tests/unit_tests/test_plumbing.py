# -*- coding: utf-8 -*-
"""
Tests for the MTRESS solph model.
"""

import numpy as np
from oemof.solph._plumbing import sequence

from mtress._plumbing import (maxseq, minseq)

def test_maxseq():
    a = np.array([1, 2, 4])
    b = np.array([3, 2, 1])
    c = sequence(2)
    d = sequence(5)
    e = np.array([0, np.inf, 5])
    f = np.array([0, -np.inf, 5])

    np.testing.assert_equal(maxseq(a, b), np.array([3, 2, 4]))
    np.testing.assert_equal(maxseq(a, c), np.array([2, 2, 4]))
    np.testing.assert_equal(maxseq(c, b), np.array([3, 2, 2]))
    np.testing.assert_equal(maxseq(a, e), np.array([1, np.inf, 5]))
    np.testing.assert_equal(maxseq(a, f), np.array([1, 2, 5]))

    assert maxseq(c, d) == d


def test_minseq():
    a = np.array([1, 2, 4])
    b = np.array([3, 2, 1])
    c = sequence(2)
    d = sequence(5)
    e = np.array([0, -np.inf, 5])
    f = np.array([0, np.inf, 5])

    np.testing.assert_equal(minseq(a, b), np.array([1, 2, 1]))
    np.testing.assert_equal(minseq(a, c), np.array([1, 2, 2]))
    np.testing.assert_equal(minseq(c, b), np.array([2, 2, 1]))
    np.testing.assert_equal(minseq(c, b), np.array([2, 2, 1]))
    np.testing.assert_equal(minseq(a, e), np.array([0, -np.inf, 4]))
    np.testing.assert_equal(minseq(a, f), np.array([0, 2, 4]))

    assert minseq(c, d) == c
