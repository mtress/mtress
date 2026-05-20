from oemof.network.network.nodes import QualifiedLabel

from ..._subnetwork import SubNetwork


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
