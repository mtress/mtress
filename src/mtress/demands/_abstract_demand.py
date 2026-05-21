"""Abstract demand class to ensure a unified interface."""

from oemof.network.network.nodes import QualifiedLabel

from .._subnetwork import SubNetwork


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
