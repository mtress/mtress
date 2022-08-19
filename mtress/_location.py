"""Locations in a meta model."""

from oemof import solph

from . import carriers, demands, technologies


class Location:
    """Location of a MTRESS meta model."""

    def __init__(self, name: str, config: dict, meta_model):
        """
        Create location instance.

        :param name: User friendly name of the location
        :param config: Configuration dict for this location
        :param meta_model: Reference to the meta model
        """
        self._name = name
        self._meta_model = meta_model

        # Initialize energy carriers
        self._carriers = {}
        for carrier_name, carrier_config in config.get("carriers", {}).items():
            assert hasattr(
                carriers, carrier_name
            ), f"Energy carrier {carrier_name} not implemented"

            cls = getattr(carriers, carrier_name)
            self._carriers[cls] = cls(location=self, **carrier_config)

        # Initialize demands
        self._demands = {}
        for demand_name, demand_config in config.get("demands", {}).items():
            assert hasattr(
                demands, demand_name
            ), f"Demand {demand_name} not implemented"

            cls = getattr(demands, demand_name)
            self._demands[cls] = cls(location=self, **demand_config)

        self._components = {}
        for component_name, component_config in config.get("components", {}).items():
            technology_name = component_config["technology"]
            assert hasattr(
                technologies, technology_name
            ), f"Technology {technology_name} not implemented"

            cls = getattr(technologies, technology_name)
            self._components[component_name] = cls(
                name=component_name, location=self, **component_config["parameters"]
            )

        # After all components have been added, add interconnections
        for _, component in self._components.items():
            component.add_interconnections()

    def add_constraints(self, model: solph.Model):
        """Add constraints to the model."""
        for _, component in self._components.items():
            component.add_constraints(model)

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
            obj for _, obj in self._components.items() if isinstance(obj, technology)
        ]
