"""
Basic example to show that it's possible to define the values you want to apply
when there is excess or missing heat

"""

import os
from oemof.solph import Results

from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress._helpers import get_flow_units, get_energy_types

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.HeatCarrier(temperature_levels=[10, 20, 30, 40, 55]))
house_1.add(
    demands.FixedTemperatureHeating(
        name="space_heating",
        min_flow_temperature=30,
        return_temperature=20,
        time_series=[50],
    )
)

# set penalty here
house_1.add(technologies.SlackNode(penalty=10))

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 01:00:00",
        "freq": "60min",
    },
)

solph_representation.build_solph_model()

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
mr = Results(solved_model)
flows = mr["flow"]
units = get_flow_units(solph_representation)
flow_colours = get_energy_types(solph_representation)

# Print the objective value.
# Here it contains the cost of the operation including penalties.
# print(mr["objective"])
solph_representation.graph(
    flow_results=flows, units=units, flow_colours=flow_colours
)
