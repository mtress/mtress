"""Abstract carrier class to ensure a unified interface."""

import numpy as np

from .._subnetwork import SubNetwork


class AbstractCarrier(SubNetwork):
    """Abstract carrier class to ensure a unified interface."""

    def __init__(self, label=None, *, parent_node=None, custom_properties=None,):
        """Initialize carrier."""
        if label is None:
            label = self.__class__.__name__
        super().__init__(
            label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )


class AbstractLayeredCarrier(AbstractCarrier):
    """
    Abstract carrier with multiple levels.

    This acts as a base class for heat layered energy or substance
    carriers, i.e. heat with multiple temperature levels.
    """

    def __init__(self, *, levels, **kwargs):
        """Initialize carrier.

        :param levels: Sorted (ascending) quality levels
        """
        super().__init__(**kwargs)

        self._levels = levels

    def get_surrounding_levels(self, level):
        return self._get_surrounding_levels(level, self._levels)

    @staticmethod
    def _get_surrounding_levels(level, levels):
        """Get the next bigger and smaller level."""
        if level in levels:
            return level, level

        # Extend levels by positive and negative infinity to prevent
        # index errors
        levels = np.concatenate(([-np.inf], levels, [np.inf]))
        i = np.searchsorted(levels, level)
        return levels[i - 1], levels[i]

    @property
    def levels(self):
        """Return levels of carrier."""
        return self._levels

    def get_levels_between(self, minimum, maximum):
        """Returns the levels existing in a closed interval."""

        if minimum > maximum:
            raise ValueError(
                "Minimum level must be smaller or equal to the maximum level."
            )
        if minimum in self.levels:
            min_index = self.levels.index(minimum)
        else:
            min_index = np.searchsorted(self.levels, minimum)

        if maximum in self.levels:
            max_index = self.levels.index(maximum) + 1
        else:
            max_index = np.searchsorted(self.levels, maximum)

        return self.levels[min_index:max_index]
