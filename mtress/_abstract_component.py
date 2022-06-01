"""Abstract MTRESS components."""

from abc import ABC

from oemof import solph

PREFIXES = {
    solph.Bus: "b",
    solph.Sink: "d",
    solph.Source: "s",
    solph.Transformer: "t",
    solph.GenericStorage: "st",
}


class AbstractComponent(ABC):
    """Abstract MTRESS component."""

    def __init__(self, location, name):
        """Initialize a generic MTRESS component."""
        self._location = location
        self._name = name

    def _generate_label(self, element, identifier):
        """Generate a unique label for the generated solph components."""
        prefix = PREFIXES.get(element, "n")
        return f"{self._location.name}:{self._name}:{prefix}_{identifier}"

    @property
    def name(self):
        """Return name of MTRESS component."""
        return self._name
