"""Abstract demand class to ensure a unified interface."""

from .._abstract_component import AbstractComponent


class AbstractDemand(AbstractComponent):
    """
    Abstract demand class to ensure a unified interface.

    All subclasses have to implement the `__prepare` method and the
    `_add_solph_components` method.
    """

    def __init__(self, location):
        """Initialize demand."""
        super().__init__(location, "d_" + self.__class__.__name__.lower())
