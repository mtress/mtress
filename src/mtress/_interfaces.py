"""Helper interfaces for MTRESS elements."""

from abc import ABC
from oemof.network import Node


class NamedElement(ABC):
    """Named MTRESS element."""

    def __init__(self, name: str) -> None:
        """Initialize named element."""
        self._name = name
        self._nesting_element = None
        self._node = None

    @property
    def node(self) -> Node:
        """Return node that represents the current element"""
        return self._node

    @property
    def name(self) -> str:
        """Return name."""
        return self._name

    def build_core(self) -> None:
        """Build the core structure of the component."""
