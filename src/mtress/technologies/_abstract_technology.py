"""Abstract technology class to ensure a unified interface."""

from oemof.network.network.nodes import QualifiedLabel

from .._subnetwork import SubNetwork


class AbstractTechnology(SubNetwork):
    """Abstract technology class to ensure a unified interface."""

    def __init__(
        self,
        *,
        location=None,
        custom_properties=None,
    ):
        """Initialize technology."""

        label = self.__class__.__name__
        if location:
            if isinstance(location.label, QualifiedLabel):
                label = QualifiedLabel([label, *location.label])
            else:
                label = QualifiedLabel([label, location.label])
        super().__init__(
            label,
            parent_node=location,
            custom_properties=custom_properties,
        )
