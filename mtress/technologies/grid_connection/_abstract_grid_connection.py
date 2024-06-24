from mtress._abstract_component import AbstractComponent


class AbstractGridConnection(AbstractComponent):
    """Abstract carrier class to ensure a unified interface."""

    def __init__(self, **kwargs):
        super().__init__(name=self.__class__.__name__, **kwargs)
