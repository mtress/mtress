"""Locations in a meta model."""

from ._constants import EnergyType
from ._base_mtress_nodes import SubNetwork
from ._carriers._layered_carrier import AbstractCarrier
from .technologies._abstract_technology import AbstractTechnology


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

    def __init__(
        self,
        label,
        *,
        parent_node=None,
        custom_properties=None,
    ) -> None:
        """
        Create location instance.

        :param name: User friendly name of the location
        """
        super().__init__(
            label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

    def get_interfaces(self, et: EnergyType):
        # collect all in- and outbound interfaces of given EnergyType
        interfaces = []
        for sn in self.subnodes:
            i_i = sn.inbound_interfaces.get(et, [])
            interfaces += i_i
            o_i = sn.outbound_interfaces.get(et, [])
            interfaces += o_i
        for i in interfaces:
            yield i

    def get_carrier(
        self,
        carrier,
    ) -> AbstractCarrier:
        """
        Return the energy carrier object.

        :param carrier: Carrier type to obtain
        """
        for sn in self.subnodes:
            if isinstance(sn, carrier):
                return sn

        return self.subnode(
            carrier,
            local_name=carrier.__name__,
        )

    def get_technology(
        self,
        technology,
    ) -> AbstractTechnology:
        """
        Get components by technology.

        :param technology: Technology type
        """
        return [sn for sn in self.subnodes if isinstance(sn, technology)]

    def establish_interconnections(self):
        pass
