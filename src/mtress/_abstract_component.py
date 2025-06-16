"""Abstract MTRESS components."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from ._interfaces import NamedElement
from ._solph_model import SolphModel

if TYPE_CHECKING:
    from ._location import Location


class AbstractComponent(NamedElement):
    """Abstract MTRESS component."""

    def __init__(self, name: str, autoconnect: bool = True) -> None:
        """Initialize a generic MTRESS component."""
        super().__init__(name)
        self.autoconnect = autoconnect
        self._location = None

        self._solph_nodes: list = []
        self._solph_model: SolphModel = None

    @property
    def location(self):
        """Return location this component belongs to."""
        return self._location

    def register_location(self, location: Location):
        """Register this component to a location."""
        if self._location is not None:
            raise KeyError("Location already registered")

        self._nesting_element = location
        self._location = location

    def register_solph_model(self, solph_model: SolphModel) -> None:
        """Store a reference to the solph model."""
        if self._solph_model is not None:
            raise KeyError("SolphModel already registered")

        self._solph_model = solph_model

    def create_solph_node(self, label: str, node_type: Callable, **kwargs):
        """Create a solph node and add it to the solph model."""
        _full_label = tuple(self.create_label(label))

        if label in self._solph_nodes:
            raise KeyError(
                f"Solph component named {_full_label} already exists"
            )

        _node = node_type(label=_full_label, **kwargs)

        # Store a reference to the MTRESS component
        setattr(_node, "mtress_component", self)
        setattr(_node, "short_label", label)

        self._solph_nodes.append(_node)
        self._solph_model.energy_system.add(_node)

        return _node

    @property
    def solph_nodes(self) -> list:
        """Iterate over solph nodes."""
        return self._solph_nodes

    def build_core(self) -> None:
        """Build the core structure of the component."""

    def establish_interconnections(self) -> None:
        """Build interconnections with other nodes."""

    def add_constraints(self) -> None:
        """Add constraints to the model."""
