"""Abstract energy carrier class to ensure a unified interface."""

from .._abstract_component import AbstractComponent


class AbstractCarrier(AbstractComponent):
    """
    Abstract energy carrier class to ensure a unified interface.

    All subclasses have to implement the `__prepare` method and the
    `_add_solph_components` method.
    """

    def __init__(self, location):
        """Initialize energy carrier."""
        super().__init__(location, "ec_" + self.__class__.__name__.lower())
