"""Abstract carrier class to ensure a unified interface."""


import numpy as np

from .._abstract_component import AbstractComponent


class AbstractCarrier(AbstractComponent):
    """Abstract carrier class to ensure a unified interface."""

    def __init__(self):
        """Initialize carrier."""
        super().__init__("c_" + self.__class__.__name__.lower())


class AbstractLayeredCarrier(AbstractCarrier):
    """
    Abstract carrier with multiple levels.

    This acts as a base class for layered energy or substance carriers, i.e.
    heat with multiple temperature levels or gases with multiple pressure levels.
    """

    def __init__(self, levels):
        """Initialize carrier."""
        super().__init__()

        self._levels = np.unique(levels)

    def get_surrounding_levels(self, level):
        """Get the next bigger and smaller level."""
        if level in self._levels:
            return level, level

        # Extend levels by positive and negative infinity to prevent index errors
        _levels = np.concatenate(([np.NINF], self._levels, [np.PINF]))
        i = np.searchsorted(_levels, level)
        return _levels[i - 1], _levels[i]

    @property
    def levels(self):
        """Return levels of carrier."""
        return self._levels
