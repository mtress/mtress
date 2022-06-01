"""Abstract energy carrier class to ensure a unified interface."""

from .._abstract_component import AbstractComponent


class AbstractEnergyCarrier(AbstractComponent):
    """
    Abstract energy carrier class to ensure a unified interface.

    All subclasses have to implement the `__prepare` method and the
    `_add_solph_components` method.
    """

    def __init__(self, location, energy_system):
        """Initialize energy carrier."""
        super().__init__(location, "ec_" + self.__class__.__name__.lower())

        # Store a reference to the energy system
        self._energy_system = energy_system
