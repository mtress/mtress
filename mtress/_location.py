"""Locations in a meta model."""

from curses import meta
from typing import Optional

from oemof import solph

from . import carriers as mt_carriers
from . import demands as mt_demands
from . import technologies as mt_technologies
from ._abstract_component import AbstractComponent
from .carriers._abstract_carrier import AbstractCarrier
from .demands._abstract_demand import AbstractDemand


class Location:
    """Location of a MTRESS meta model."""

    def __init__(self, name: str):
        """
        Create location instance.

        :param name: User friendly name of the location
        :param config: Configuration dict for this location
        :param meta_model: Reference to the meta model
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
        self._carriers[type(carrier)] = carrier

    def add_demand(self, demand: AbstractDemand):
        self._demands[type(demand)] = demand

    def add_component(self, component: AbstractComponent):
        self._technologies[type(component)] = component

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

    def get_components(self, technology: type):
        """
        Get components by technology.

        :param technology: Technology type
        """
        return [
            obj for _, obj in self._components.items() if isinstance(obj, technology)
        ]
