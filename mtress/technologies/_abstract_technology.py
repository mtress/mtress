"""Base class for MTRESS technologies."""

from abc import ABC, abstractmethod
from enum import Enum, auto

from oemof import solph

from .._abstract_component import AbstractComponent


class FlowType(Enum):
    """Types/categories for oemof flows."""

    ALL = auto()
    IN = auto()
    OUT = auto()
    PRODUCTION = auto()
    STORAGE = auto()
    EXPORT = auto()
    IMPORT = auto()
    RENEWABLE = auto()


class AbstractTechnology(AbstractComponent):
    """Base class for MTRESS technologies."""

    def __init__(self, name):
        """Initialize technology."""
        super().__init__(name)
        self._flows = None

    def build(self):
        self._flows = {flow_type: set() for flow_type in FlowType}

    def add_interconnections(self):
        """
        Add technology interconnections.

        Some technologies require interconnections, e.g. an ice storage
        connects to a heat pump. These interconnections have to be made
        after creation of the technologies.
        """

    def add_constraints(self, model: solph.Model):
        """
        Add model constraints.

        Some technologies require constraints, e.g. a shared limit on a
        storage with multiple temperature levels. These constraints can
        not be created prior to the model generation.
        """
        pass

    def categorise_flow(self, flow, flow_types):
        """Categorise given flow under the named flow_types."""
        for flow_type in flow_types | {FlowType.ALL}:
            if flow_type in self._flows:
                self._flows[flow_type].add(flow)
            else:
                self._flows[flow_type] = {flow}

    def get_flows(self, flow_types):
        """Return flows categorised under all named flow_types."""
        flows = self._flows[FlowType.ALL].copy()

        for flow_type in flow_types:
            try:
                flows.intersection_update(self._flows[flow_type])
            except KeyError:
                return set()

        return flows


class AbstractAnergySource(ABC):
    """Interface class for anergy providing technologies.

    Functionality/Notice: There can be several anergy sources, such as
        a down hole heat exchanger or air source heat exchanger.
        They hold a time series for both the temperature and the
        power limit that can be drawn from the source. Additionally
        a total limit can be defined, which is particularly
        important for geothermal sources that need to recover.

    """

    @property
    @abstractmethod
    def temperature(self):
        """Return anergy temperature level."""

    @property
    @abstractmethod
    def bus(self):
        """Return oemof bus to connect to."""
