"""
Basic example to show that it's possible to define the values you want to apply
when there is excess or missing heat
 
"""

import os

from oemof.solph.processing import results, meta_results

from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress._helpers import get_flows

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[10, 20, 30, 40, 55],
        reference_temperature=0,
        missing_heat_penalty=10,
        excess_heat_penalty=10,
    )
)
house_1.add(
    demands.FixedTemperatureHeating(
        name="space_heating",
        min_flow_temperature=30,
        return_temperature=20,
        time_series=[50],
    )
)

house_1.add(technologies.Slack())

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 01:00:00",
        "freq": "60T",
    },
)

solph_representation.build_solph_model()

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

myresults = results(solved_model)
flows = get_flows(myresults)

plot = solph_representation.graph(detail=True, flow_results=flows)
plot.render(outfile="specify_penalties.png")

mr = meta_results(solved_model)

# Print the objective value.
# Here it contains the cost of the operation including penalties.
print(mr["objective"])
