from oemof.network.network.nodes import QualifiedLabel

from ..._subnetwork import SubNetwork

from abc import abstractmethod


class AbstractGridConnection(SubNetwork):
    """Abstract carrier class to ensure a unified interface."""

    def __init__(
        self,
        *,
        location=None,
        custom_properties=None,
    ):

        label = self.__class__.__name__
        if location:
            if isinstance(location.label, QualifiedLabel):
                label = QualifiedLabel([label, *location.label])
            else:
                label = QualifiedLabel([label, location.label])
        super().__init__(
            label=label,
            parent_node=location,
            custom_properties=custom_properties,
        )

    @abstractmethod
    def _connect(self, other: AbstractGridConnection):
        pass

    def connect(self, other: AbstractGridConnection):
        if self.__class__ != other.__class__:
            raise TypeError("GridConnections need to be of same type")

        self._connect(other=other)
