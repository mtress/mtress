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

    def __init__(self, *, levels, **kwargs):
        """Initialize carrier."""
        super().__init__(**kwargs)

        self._levels = levels

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

class AbstractLayeredGasCarrier(AbstractCarrier):
    """
    Abstract layered gas carrier with multiple levels.

    This acts as a base class for gas carriers, i.e.
    gases with multiple input_pressure levels.wh
    """

    def __init__(self, *, gas_type, pressures, **kwargs):
        """Initialize carrier."""
        super().__init__(**kwargs)
        self._pressures = {gas: np.unique(levels) for gas, levels in zip(gas_type, pressures)}
        self._gas_type = gas_type

    def get_surrounding_levels(self, pressure_level):
        """Get the next bigger and smaller level for each gas."""
        surrounding_levels = {}
        for gas, levels in self._pressures.items():
            if pressure_level in levels:
                surrounding_levels[gas] = (pressure_level, pressure_level)
            else:
                _levels = np.unique(levels)
                _pressure_levels = np.concatenate(([np.NINF], _levels, [np.PINF]))
                i = np.searchsorted(_pressure_levels, pressure_level)
                surrounding_levels[gas] = (_pressure_levels[i - 1], _pressure_levels[i])

        return surrounding_levels

    @property
    def pressure_levels(self):
        """Return input_pressure level of gas carrier"""
        return self._pressures

    @property
    def gas_type(self):
        return self._gas_type