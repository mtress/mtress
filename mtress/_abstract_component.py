"""Abstract MTRESS components."""

from abc import ABC, abstractmethod

from ._meta_model import SolphModel


class AbstractComponent(ABC):
    """Abstract MTRESS component."""

    def __init__(self, name: str):
        """Initialize a generic MTRESS component."""
        self._name = name
        self._location = None

    def assign_location(self, location):
        """Assign component to a location."""
        self._location = location

    @property
    def identifier(self) -> list:
        """Return identifier of this component."""
        return [self.location.name, self.name]

    @property
    def name(self):
        """Return name of MTRESS component."""
        return self._name

    @property
    def location(self):
        """Return location this component belongs to."""
        return self._location

    @property
    def meta_model(self):
        """Return meta model this component belongs to."""
        return self.location.meta_model


class AbstractSolphComponent(ABC):
    """Interface for components which can be represented in `oemof.solph`."""

    _solph_model: SolphModel = None

    @property
    @abstractmethod
    def identifier(self) -> list:
        """Get identifier of component."""

    def register_solph_model(self, solph_model: SolphModel):
        """Store a reference to the solph model."""
        if self._solph_model is not None:
            raise Exception("SolphModel already registered")

        self._solph_model = solph_model

    def build_core(self):
        """Build the core structure of the component."""

    def establish_interconnections(self):
        """Build interconnections with other components."""

    def add_constraints(self):
        """Add constraints to the model."""

    # TODO: Methods for result analysis


class ModelicaInterface(ABC):  # pylint: disable=too-few-public-methods
    """Interface for components which can be represented in open modelica."""

    # At the moment, this is just a memory aid
