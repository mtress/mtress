"""Abstract carrier class to ensure a unified interface."""


import numpy as np

from .._abstract_component import AbstractComponent


class AbstractCarrier(AbstractComponent):
    """Abstract carrier class to ensure a unified interface."""

    def __init__(self, **kwargs):
        """Initialize carrier."""
        super().__init__(name=self.__class__.__name__, **kwargs)


class AbstractLayeredCarrier(AbstractCarrier):
    """
    Abstract carrier with multiple levels.

    This acts as a base class for heat layered energy or substance
    carriers, i.e. heat with multiple temperature levels.
    """

    def __init__(self, *, levels, reference, **kwargs):
        """Initialize carrier.

        :param levels: Sorted (ascending) quality levels
        :param refernece: value of reference quality
        """
        super().__init__(**kwargs)

        self._levels = levels
        self._reference = reference

    def get_surrounding_levels(self, level):
        return self._get_surrounding_levels(level, self._levels)

    @staticmethod
    def _get_surrounding_levels(level, levels):
        """Get the next bigger and smaller level."""
        if level in levels:
            return level, level

        # Extend levels by positive and negative infinity to prevent index errors
        levels = np.concatenate(([np.NINF], levels, [np.PINF]))
        i = np.searchsorted(levels, level)
        return levels[i - 1], levels[i]

    @property
    def levels(self):
        """Return levels of carrier."""
        return self._levels

    def get_levels_between(self, minimum, maximum):
        levels = np.concatenate(([np.NINF], self.levels, [np.PINF]))
        min_index = np.searchsorted(levels, minimum) - 1
        max_index = np.searchsorted(levels, maximum)
        return self.levels[min_index:max_index]

    @property
    def reference(self):
        return self._reference

    @property
    def reference_level(self):
        """Return index or key of reference level"""
        raise NotImplementedError
