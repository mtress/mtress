"""Helper interfaces for MTRESS elements."""

import re
from abc import ABC, abstractmethod


class NamedElement(ABC):
    """Named MTRESS element."""

    def __init__(self, name: str) -> None:
        """Initialize named element."""
        self._name = name

        # TODO: Improve this?
        self._slug = re.sub(r"[^a-zA-Z0-9]+", "", name)

    @property
    def name(self) -> str:
        """Return name."""
        return self._name

    @property
    def slug(self) -> str:
        """Return slug."""
        return self._slug

    @property
    @abstractmethod
    def identifier(self) -> str:
        """Return identifier."""
