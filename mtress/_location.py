"""Locations in a meta model."""


from ._abstract_component import AbstractComponent
from .carriers._abstract_carrier import AbstractCarrier
from .demands._abstract_demand import AbstractDemand


class Location:
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

    def __init__(self, name: str):
        """
        Create location instance.

        :param name: User friendly name of the location
        """
        self._name = name
        self._meta_model = None

        self._carriers = {}
        self._technologies = {}
        self._demands = {}

    def assign_meta_model(self, meta_model):
        """Store reference to meta model."""
        self._meta_model = meta_model

    def add_carrier(self, carrier: AbstractCarrier):
        """Add a carrier to the location."""
        carrier.register_location(self)
        self._carriers[type(carrier)] = carrier
        carrier.register(self)

    def add_demand(self, demand: AbstractDemand):
        """Add a demand to the location."""
        demand.register_location(self)
        self._demands[type(demand)] = demand
        demand.register(self)

    def add_technology(self, technology: AbstractComponent):
        """Add a demand to the location."""
        technology.register_location(self)
        self._technologies[technology.name] = technology

    @property
    def name(self):
        """Return name of the location."""
        return self._name

    @property
    def meta_model(self):
        """Return meta model this location belongs to."""
        return self._meta_model

    def get_carrier(self, carrier: type):
        """
        Return the energy carrier object.

        :param carrier: Carrier type to obtain
        """
        return self._carriers[carrier]

    def get_demand(self, demand: type):
        """
        Return demand object.

        :param demand: Demand type
        """
        return self._demands[demand]

    def get_technology(self, technology: type):
        """
        Get components by technology.

        :param technology: Technology type
        """
        return [
            obj for _, obj in self._technologies.items() if isinstance(obj, technology)
        ]

    @property
    def carriers(self):
        """Get all carriers of this location."""
        return self._carriers.values()

    @property
    def demands(self):
        """Get all demands of this location."""
        return self._demands.values()

    @property
    def technologies(self):
        """Get all technologies of this location."""
        return self._technologies.values()
