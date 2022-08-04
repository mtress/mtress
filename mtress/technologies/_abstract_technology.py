"""Base class for MTRESS technologies."""

from abc import ABC, abstractmethod

from oemof import solph

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

    def add_constraints(self, model: solph.Model):
        """
        Add model constraints.

        Some technologies require constraints, e.g. a shared limit on a
        storage with multiple temperature levels. These constraints can
        not be created prior to the model generation.
        """


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
