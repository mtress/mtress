"""Helper interfaces for MTRESS elements."""

from abc import ABC, abstractmethod


class NamedElement(ABC):
    """Named MTRESS element."""

    def __init__(self, name: str) -> None:
        """Initialize named element."""
        self._name = name
        self._nesting_element = None

    @property
    def name(self) -> str:
        """Return name."""
        return self._name

    def create_label(self, label: str) -> list[str]:
        """Return a unique label based on the identifier."""
        return self.identifier + [label]

    @property
    def identifier(self) -> list[str]:
        """Return identifier."""
        identifier = []
        highest_level = self
        while highest_level is not None:
            identifier.append(highest_level.name)
            highest_level = highest_level._nesting_element

        identifier.reverse()
        return identifier
