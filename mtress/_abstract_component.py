"""Abstract MTRESS components."""

from abc import ABC

from oemof import solph


class AbstractComponent(ABC):
    """Abstract MTRESS component."""

    def __init__(self, name: str):
        """Initialize a generic MTRESS component."""
        self._name = name
        self._location = None

    def assign_location(self, location):
        """Assign component to a location."""
        self._location = location

    def _generate_label(self, identifier):
        """Generate a unique label for a subcomponent."""
        return f"{self.location.name}:{self.name}:{identifier}"

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


class AbstractSolphComponent(AbstractComponent):
    """Interface for components which can be represented in `oemof.solph`."""

    def __init__(self, name: str):
        """Initialize solph interface."""
        super().__init__(name)
        self._solph_components: list = []

    def build_core(self):
        """Build the core structure of the component."""

    def establish_interconnections(self):
        """Build interconnections with other components."""

    def add_constraints(self, model: solph.Model):
        """Add constraints to the model."""

    def _add_solph_component(self, component, label, **kwargs):
        """Add oemof solph components to the energy system."""
        _component = component(label=self._generate_label(label), **kwargs)

        self._solph_components.append(_component)
        self.meta_model.energy_system.add(_component)


class AbstractModelicaComponent(AbstractComponent):
    """Interface for components which can be represented in open modelica."""
