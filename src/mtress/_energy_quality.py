# -*- coding: utf-8 -*-
"""Specifications of different types of energy

SPDX-FileCopyrightText: Deutsches Zentrum für Luft- und Raumfahrt e.V. (DLR)

SPDX-License-Identifier: MIT
"""

import sys

from oemof.solph._plumbing import Apply, sequence

from ._plumbing import sequence_equal


class EnergyQuality:
    """energy quality"""

    _value = Apply(sequence)
    _minimum = Apply(sequence)
    _maximum = Apply(sequence)

    infere = object()

    def __init__(
        self,
        value,
        minimum=None,
        maximum=None,
        fixed=infere,
    ):
        if fixed is self.infere:
            fixed = minimum is None and maximum is None
        elif fixed == True:
            if minimum is not None or maximum is not None:
                raise ValueError(
                    "Argument 'fixed' cannot be true"
                    + " if minimum or maximum is set."
                )
        # We always need a value to be able to use the quality for preliminary
        # calculations (i.e. before establish_interconnection).
        self._value = value
        self.minimum = minimum
        self.maximum = maximum
        self.fixed = fixed

    @property
    def minimum(self):
        if self.fixed:
            return self._value
        elif self._minimum is not None:
            return self._minimum
        else:
            return -sys.float_info.max

    @minimum.setter
    def minimum(self, value):
        # TODO: forbid overwriting final values
        self._minimum = value

    @property
    def maximum(self):
        if self.fixed:
            return self._value
        elif self._maximum is not None:
            return self._maximum
        else:
            return sys.float_info.max

    @maximum.setter
    def maximum(self, value):
        # TODO: forbid overwriting final values
        self._maximum = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not self.fixed:
            self.fixed = True
            self._value = value
        else:
            raise RuntimeError(
                "Tried to change the value of an 'EnergyQuality' that has a"
                + " fixed value. (Setting a value after initialisation fixes"
                + " that value)."
            )

    def __eq__(self, other):
        return (
            sequence_equal(self.minimum, other.minimum)
            and sequence_equal (self.maximum, other.maximum)
        )
