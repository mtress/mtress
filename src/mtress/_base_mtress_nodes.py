from abc import ABC, abstractmethod

from oemof import solph
from oemof.network import Node

from ._energy_types import EnergyType


class SubNetwork(ABC, Node):
    # TODO: documentation
    def __init__(
        self,
        label,
        *,
        parent_node=None,
        custom_properties=None,
    ) -> None:
        super().__init__(
            label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        self.inbound_interfaces: dict[
            type[AbstractCarrier] : list[solph.Bus]
        ] = {}
        self.outbound_interfaces: dict[
            type[AbstractCarrier] : list[solph.Bus]
        ] = {}

    @abstractmethod
    def establish_interconnections(self):
        """Interconnect with other parts of the `mtress.EnergySystem`.

        Implementations collect information from other parts of the
        `mtress.EnergySystem` and autoconnect based on that information.
        Even if information from other parts was available on initialisation
        (e.g. because a parent node is a specific mtress class), it should only
        be collected and considered at this point, when the system and all its
        componentents are considered "final" by the user.

        On initialisation, we build based on local information and are
        completely compatible to a `solph.EnergySystem`, even if this means we
        have to a alter subnodes in `establish_interconnections`.
        """

        pass

    def add_constraints(self, model: solph.Model):
        pass


class AbstractCarrier(SubNetwork):
    """Abstract carrier class to ensure a unified interface."""

    def __init__(
        self,
        label,
        *,
        parent_node,
        custom_properties,
    ):
        """Initialize carrier."""

        super().__init__(
            label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )


class AbstractDemand(SubNetwork):
    """
    Abstract demand class to ensure a unified interface.
    """

    def __init__(
        self,
        label,
        *,
        parent_node=None,
        custom_properties=None,
    ):
        super().__init__(
            label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )


class AbstractTechnology(SubNetwork):
    """Abstract technology class to ensure a unified interface."""

    def __init__(
        self,
        label,
        *,
        parent_node=None,
        custom_properties=None,
    ):
        """Initialize technology."""
        super().__init__(
            label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )
