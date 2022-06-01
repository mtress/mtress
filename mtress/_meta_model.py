from oemof import solph

from . import energy_carriers
# from . import technologies

class Location:
    def __init__(self, name: str, energy_system: solph.EnergySystem, config: dict, meta_model):
        self._name = name
        self._meta_model = meta_model
        self._energy_system = energy_system

        self.energy_carriers = {}
        for ec_name, ec_config in config["energy_carriers"].items():
            assert hasattr(energy_carriers, ec_name), f"Energy carrier {ec_name} not implemented"

            print(ec_name)
            ec_cls = getattr(energy_carriers, ec_name)
            print(ec_cls)
            self.energy_carriers[ec_name] = ec_cls(location=self, energy_system=energy_system, **ec_config)

        # self.technologies = {}
        # for tech_name, tech_config in config.get("technologies", {}):
        #     tech = tech_config.get("technology")

        #     assert hasattr(technologies, tech), f"Technology {tech} not implemented"
        #     tech_cls = getattr(technologies, tech)

        #     cfg = tech_config.get("parameters")
        #     self.technologies[tech_name] = tech_cls(name=tech_name, location=self, energy_system=energy_system, **cfg)


        # # After all technologies have been added to the location we add interconnections
        # # e.g. connect anergy sources to heat pumps
        # for tech in self.technologies:
        #     tech.add_interconnections()

    @property
    def name(self):
        """Return name of the location."""
        return self._name
    


# class MetaModel:

#     def __init__(self, config):
#         self._locations = {}

#         for location_name, location_config in config["locations"].items():
#             self._locations[location_name] = Location(config=location_config, meta_model=self)




