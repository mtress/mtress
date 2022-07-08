"""Base class for MTRESS technologies."""

from abc import ABC, abstractmethod

from .._abstract_component import AbstractComponent


class AbstractTechnology(AbstractComponent):
    """Base class for MTRESS technologies."""

    def add_interconnections(self):
        """
        Add technology interconnections.

        Some technologies require interconnections, e.g. an ice storage
        connects to a heat pump. These interconnections have to be made
        after creation of the technologies.
        """
        pass


class AbstractAnergySource(ABC):
    """Base class for anergy providing technologies."""

    @property
    @abstractmethod
    def temperature(self):
        """Return anergy temperature level."""
        pass

    @property
    @abstractmethod
    def bus(self):
        """Return oemof bus to connect to."""
        pass
