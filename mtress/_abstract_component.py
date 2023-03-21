"""Abstract MTRESS components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

from ._meta_model import SolphModel

if TYPE_CHECKING:
    from ._location import Location


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

    def register_location(self, location: Location):
        """Register this component to a location."""
        if self._location is not None:
            raise Exception("Location already registered")

        self._location = location

    @property
    def meta_model(self):
        """Return meta model this component belongs to."""
        return self.location.meta_model


class AbstractSolphComponent(ABC):
    """Interface for components which can be represented in `oemof.solph`."""

    _solph_components: dict = {}
    _solph_model: SolphModel = None

    @property
    @abstractmethod
    def identifier(self) -> list:
        """Get identifier of component."""

    def register_solph_model(self, solph_model: SolphModel) -> None:
        """Store a reference to the solph model."""
        if self._solph_model is not None:
            raise Exception("SolphModel already registered")

        self._solph_model = solph_model

    def create_solph_component(self, label: str, component: Callable, **kwargs):
        """Create a solph component and add it to the solph model."""
        _full_label = self._solph_model.generate_label(self, label)

        if label in self._solph_components:
            raise KeyError(f"Solph component named {_full_label} already exists")

        _component = component(label=_full_label, **kwargs)
        self._solph_components[label] = _component
        self._solph_model.energy_system.add(_component)

        return _component

    def build_core(self) -> None:
        """Build the core structure of the component."""

    def establish_interconnections(self) -> None:
        """Build interconnections with other components."""

    def add_constraints(self) -> None:
        """Add constraints to the model."""

    # TODO: Methods for result analysis


class ModelicaInterface(ABC):  # pylint: disable=too-few-public-methods
    """Interface for components which can be represented in open modelica."""

    # At the moment, this is just a memory aid
