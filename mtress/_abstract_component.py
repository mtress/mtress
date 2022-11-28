"""Abstract MTRESS components."""

from abc import ABC, abstractmethod
from typing import Callable, final

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

    @property
    @abstractmethod
    def identifier(self) -> list:
        """Get identifier of component."""

    def _full_label(self, label: str):
        """Get the unique identifier for a label."""
        return ":".join([*self.identifier, label])

    # This method is to be used in the following three functions
    def _add_solph_component(
        self, solph_model: SolphModel, component: Callable, label: str, **kwargs
    ) -> object:
        """Add oemof solph components to the energy system."""
        _full_label = self._full_label(label)
        if _full_label in solph_model.components:
            raise KeyError(f"Solph component named {label} already exists")

        solph_model.components[_full_label] = _component = component(
            label=self._full_label(label), **kwargs
        )
        solph_model.energy_system.add(_component)

        return _component

    def get_solph_component(self, solph_model: SolphModel, label: str):
        """Get the a solph component by label."""
        return solph_model.components[self._full_label(label)]

    def build_core(self, solph_model: SolphModel):
        """Build the core structure of the component."""

    def establish_interconnections(self, solph_model: SolphModel):
        """Build interconnections with other components."""

    def add_constraints(self, solph_model: SolphModel):
        """Add constraints to the model."""


class ModelicaInterface(ABC):  # pylint: disable=too-few-public-methods
    """Interface for components which can be represented in open modelica."""

    # This is just a memory aid
