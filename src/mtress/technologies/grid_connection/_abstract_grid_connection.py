from oemof.network.network.nodes import QualifiedLabel

from ..._subnetwork import SubNetwork


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
