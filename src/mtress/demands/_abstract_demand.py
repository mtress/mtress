"""Abstract demand class to ensure a unified interface."""

from oemof.network.network.nodes import QualifiedLabel

from .._subnetwork import SubNetwork


class AbstractDemand(SubNetwork):
    """
    Abstract demand class to ensure a unified interface.
    """

    def __init__(self, label, *, location=None, custom_properties=None):

        if location:
            if isinstance(location.label, QualifiedLabel):
                label = QualifiedLabel([label, *location.label])
            else:
                label = QualifiedLabel([label, location.label])

        super().__init__(
            label, parent_node=location, custom_properties=custom_properties
        )
