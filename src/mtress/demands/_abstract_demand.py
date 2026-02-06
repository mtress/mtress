"""Abstract demand class to ensure a unified interface."""

from .._subnetwork import SubNetwork


class AbstractDemand(SubNetwork):
    """
    Abstract demand class to ensure a unified interface.
    """
    def __init__(
            self,
            label,
            *,
            location=None,
            custom_properties=None):
        super().__init__(
            label,
            parent_node=location,
            custom_properties=custom_properties
        )
