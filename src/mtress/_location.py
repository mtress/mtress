"""Locations in a meta model."""

from oemof.network import Node

from ._base_mtress_nodes import AbstractCarrier, SubNetwork
from ._plumbing import TypeAccessContainer


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

        self._subnodes_by_type = TypeAccessContainer(Node)

    def get_carrier(
        self,
        carrier,
    ) -> AbstractCarrier:
        """
        Return the energy carrier object.

        :param carrier: Carrier type to obtain
        """
        if carrier in self._subnodes_by_type:
            return list(self._subnodes_by_type[carrier])[0]

        return self.subnode(
            carrier,
            local_name=carrier.__name__,
        )

    def get_nodes_by_type(
        self,
        node_type,
    ) -> set[Node]:
        """
        Get subnodes of the specified type.

        :param node_type: Technology type
        """

        if node_type in self._subnodes_by_type:
            return self._subnodes_by_type[node_type]
        else:
            return set()

    def subnode(self, class_, local_name, *args, **kwargs):
        new_node = super().subnode(class_, local_name, *args, **kwargs)
        self._subnodes_by_type.add(new_node)
        return new_node

    def establish_interconnections(self):
        pass
