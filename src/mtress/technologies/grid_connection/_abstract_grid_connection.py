from oemof.network.network.nodes import QualifiedLabel

from ..._subnetwork import SubNetwork

from abc import abstractmethod


class AbstractGridConnection(SubNetwork):
    """Abstract carrier class to ensure a unified interface."""

    def __init__(
        self,
        label,
        *,
        parent_node=None,
        custom_properties=None,
    ):
        super().__init__(
            label=label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

    @abstractmethod
    def _connect(self, other: AbstractGridConnection):
        pass

    def connect(self, other: AbstractGridConnection):
        if self.__class__ != other.__class__:
            raise TypeError("GridConnections need to be of same type")

        self._connect(other=other)
