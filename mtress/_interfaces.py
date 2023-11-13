"""Helper interfaces for MTRESS elements."""

import re
from abc import ABC, abstractmethod


class NamedElement(ABC):
    """Named MTRESS element."""

    def __init__(self, name: str) -> None:
        """Initialize named element."""
        self._name = name

    @property
    def name(self) -> str:
        """Return name."""
        return self._name

    def create_label(self, label: str) -> str:
        """Return a unique label based on the identifier."""
        return self.identifier + [label]

    @property
    @abstractmethod
    def identifier(self) -> list[str]:
        """Return identifier."""
