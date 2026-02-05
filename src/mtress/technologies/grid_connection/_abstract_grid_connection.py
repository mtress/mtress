from oemof.network.network.nodes import QualifiedLabel

from ..._subnetwork import SubNetwork


class AbstractGridConnection(SubNetwork):
    """Abstract carrier class to ensure a unified interface."""

    def __init__(
        self,
        *,
        parent_node=None,
        custom_properties=None,
    ):

        label = self.__class__.__name__
        if parent_node:
            if isinstance(parent_node.label, QualifiedLabel):
                label = QualifiedLabel([label, *parent_node.label])
            else:
                label = QualifiedLabel([label, parent_node.label])
        super().__init__(
            label=label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )
