"""Abstract MTRESS components."""

from abc import ABC

from oemof import solph


class AbstractComponent(ABC):
    """Abstract MTRESS component."""

    def __init__(self, name):
        """Initialize a generic MTRESS component."""
        self._name = name
        self._location = None

    def _generate_label(self, identifier):
        """Generate a unique label for the generated solph components."""
        return f"{self.location.name}:{self.name}:{identifier}"

    def register(self, location):
        self._location = location

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
