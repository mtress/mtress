"""Base class for MTRESS technologies."""

from .._abstract_component import AbstractComponent


class AbstractTechnology(AbstractComponent):
    """Base class for MTRESS technologies."""

    def __init__(self, **kwargs):
        """Initialize technology."""
        super().__init__(**kwargs)
