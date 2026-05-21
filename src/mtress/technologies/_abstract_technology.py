"""Abstract technology class to ensure a unified interface."""

from .._subnetwork import SubNetwork


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
