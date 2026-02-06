"""Locations in a meta model."""

from __future__ import annotations

from ._abstract_component import AbstractComponent
from ._subnetwork import SubNetwork
from .carriers._abstract_carrier import AbstractCarrier


class Location(SubNetwork):
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

    def __init__(self, label) -> None:
        """
        Create location instance.

        :param name: User friendly name of the location
        """
        super().__init__(label)

    def get_carrier(self, carrier: type) -> AbstractCarrier:
        """
        Return the energy carrier object.

        :param carrier: Carrier type to obtain
        """
        for sn in self.subnodes:
            if isinstance(sn, carrier):
                return sn
        return carrier(parent_node=self)

    def get_technology(self, technology: type) -> AbstractComponent:
        """
        Get components by technology.

        :param technology: Technology type
        """
        return [sn for sn in self.subnodes if isinstance(sn, technology)]

    def establish_interconnections(self):
        for sn in self.subnodes:
            try:
                sn.establish_interconnections()
            except AttributeError:
                raise TypeError(
                    "Only SubNetworks are allowed to be children of Location."
                )