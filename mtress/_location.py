"""Locations in a meta model."""


from typing import Dict, Iterable, Set

from ._abstract_component import AbstractComponent
from ._interfaces import NamedElement
from ._meta_model import MetaModel
from .carriers._abstract_carrier import AbstractCarrier
from .demands._abstract_demand import AbstractDemand


class Location(NamedElement):
    """
    Location in a MTRESS meta model.

    Functionality: A location is able to collect / accomodate energy
        carriers, components and demands.

    Procedure: Create a meta model first (see meta_model class).
        Afterwards create / initialize an (empty) location
        and add it to the meta model by doing the following:

        house_1 = Location(name='house_1')
        meta_model.add_location(house_1)

    Notice: To allow for automatic connections between the components
        and demands, every energy carrier (e.g. electricity or heat) and
        every component (e.g. a heat pump) can only be defined once
        per location (or left out). To define multiple instances of one
        energy carrier with different configurations, multiple locations
        have to be defined.

    Further procedure is described in the carrier and demand classes.
    """

    def __init__(self, name: str) -> None:
        """
        Create location instance.

        :param name: User friendly name of the location
        """
        super().__init__(name)
        self._meta_model: MetaModel = None

        self._carriers: Dict[type, AbstractCarrier] = {}
        self._components: Set[AbstractComponent] = set()

    @property
    def identifier(self) -> str:
        """Return an slugified identifier."""
        return self._slug

    def assign_meta_model(self, meta_model: MetaModel):
        """Store reference to meta model."""
        self._meta_model = meta_model

    def add(self, component: AbstractComponent):
        """Add a component to the location."""
        component.register_location(self)

        if isinstance(component, AbstractCarrier):
            self._carriers[type(component)] = component
        else:
            self._components.add(component)

    def add_carrier(self, carrier: AbstractCarrier):
        """Add a carrier to the location."""
        self.add(carrier)

    def add_demand(self, demand: AbstractDemand):
        """Add a demand to the location."""
        self.add(demand)

    def add_technology(self, technology: AbstractComponent):
        """Add a demand to the location."""
        self.add(technology)

    @property
    def meta_model(self):
        """Return meta model this location belongs to."""
        return self._meta_model

    def get_carrier(self, carrier: type) -> AbstractCarrier:
        """
        Return the energy carrier object.

        :param carrier: Carrier type to obtain
        """
        return self._carriers[carrier]

    def get_technology(self, technology: type) -> AbstractComponent:
        """
        Get components by technology.

        :param technology: Technology type
        """
        return [obj for obj in self._components if isinstance(obj, technology)]

    @property
    def components(self) -> Iterable[AbstractComponent]:
        """Iterate over all components."""
        for carrier in self._carriers.values():
            yield carrier

        for component in self._components:
            yield component
