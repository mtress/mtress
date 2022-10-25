"""Locations in a meta model."""

from typing import Optional
from oemof import solph

from ._abstract_component import AbstractComponent
from .carriers._abstract_carrier import AbstractCarrier
from .demands._abstract_demand import AbstractDemand
from . import carriers as mt_carriers
from . import demands as mt_demands
from . import technologies as mt_technologies


class Location:
    """Location of a MTRESS meta model."""

    def __init__(
        self,
        name: str,
        carriers: Optional[dict] = None,
        demands: Optional[dict] = None,
        components: Optional[dict] = None,
    ):
        """
        Create location instance.

        :param name: User friendly name of the location
        :param config: Configuration dict for this location
        :param meta_model: Reference to the meta model
        """
        self._name = name
        self._meta_model = None

        if carriers is None:
            carriers = dict()
        if demands is None:
            demands = dict()
        if components is None:
            components = dict()

        # Initialize energy carriers
        self._carriers = {}
        for carrier_name, carrier_config in carriers.items():
            self._create_carrier(carrier_name, carrier_config)

        # Initialize demands
        self._demands = {}
        for demand_name, demand_config in demands.items():
            self._create_demand(demand_name, demand_config)

        self._components = {}
        for component_name, component_config in components.items():
            self._create_component(component_name, component_config)

    def register(self, meta_model):
        self._meta_model = meta_model

    def build(self):
        for carrier in self._carriers.values():
            carrier.build()
        for demand in self._demands.values():
            demand.build()
        for component in self._components.values():
            component.build()

    def add_constraints(self, model: solph.Model):
        """Add constraints to the model."""
        for _, component in self._components.items():
            component.add_constraints(model)

    def _create_carrier(self, carrier_type: str, carrier_config: dict):
        assert hasattr(
            mt_carriers, carrier_type
        ), f"Energy carrier {carrier_type} not implemented"

        cls = getattr(mt_carriers, carrier_type)
        self._carriers[cls] = cls(location=self, **carrier_config)

    def _create_component(self, component_type: str, component_config: dict):
        technology_name = component_config["technology"]
        assert hasattr(
            mt_technologies, technology_name
        ), f"Technology {technology_name} not implemented"

        cls = getattr(mt_technologies, technology_name)
        self._components[component_type] = cls(
            name=component_type,
            location=self,
            **component_config["parameters"],
        )

    def _create_demand(self, demand_type: str, demand_config: dict):
        assert hasattr(
            mt_demands, demand_type
        ), f"Demand {demand_type} not implemented"

        cls = getattr(mt_demands, demand_type)
        self._demands[cls] = cls(location=self, **demand_config)

    def add_carrier(self, carrier: AbstractCarrier):
        self._carriers[type(carrier)] = carrier
        carrier.register(self)

    def add_demand(self, demand: AbstractDemand):
        self._demands[type(demand)] = demand
        demand.register(self)

    def add_component(self, component: AbstractComponent):
        self._components[type(component)] = component
        component.register(self)

    def add_interconnections(self):
        for component in self._components.values():
            component.add_interconnections()

    @property
    def name(self):
        """Return name of the location."""
        return self._name

    @property
    def energy_system(self):
        """Return reference to EnergySystem object of the metamodel."""
        return self._meta_model.energy_system

    @property
    def meta_model(self):
        """Return meta model this location belongs to."""
        return self._meta_model

    def get_carrier(self, carrier: type):
        """
        Return the energy carrier object.

        :param carrier: Carrier type to obtain
        """
        return self._carriers[carrier]

    def get_demand(self, demand: type):
        """
        Return demand object.

        :param demand: Demand type
        """
        return self._demands[demand]

    def get_components(self, technology: type):
        """
        Get components by technology.

        :param technology: Technology type
        """
        return [
            obj
            for _, obj in self._components.items()
            if isinstance(obj, technology)
        ]
