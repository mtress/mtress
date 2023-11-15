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

    def __init__(
            self, *,
            levels,
            reference,
            **kwargs):
        """Initialize carrier."""
        super().__init__(**kwargs)

        LevelType = type(levels)
        self._levels = LevelType(sorted(levels))
        self._reference = reference
        self._reference_index = self._levels.index(reference)

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

    @property
    def levels_above_reference(self):
        return self.levels[self._reference_index+1:]

    @property
    def levels_below_reference(self):
        return self.levels[:self._reference_index]

    @property
    def input_levels(self):
        """Return the list of input temperature levels."""
        return self.levels[1:]

    @property
    def output_levels(self):
        """Return the list of output temperature levels."""
        return self.levels

    @property
    def reference(self):
        return self._reference

    @property
    def reference_level(self):
        """Return index or key of reference level"""
        raise NotImplementedError
