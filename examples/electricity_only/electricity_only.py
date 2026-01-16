"""
Basic working 'electricity only' example.

Basic working 'electricity only' example which includes a location (house),
an electricity carrier which acts as a electricity source/supply from the
official grid (working price of 35 ct/kWh) as well as a demand (consumer)
with a demand time series.

At first an energy system (here meta_model) is defined with a time series
(index). Afterwards a location is defined and added to the energysystem.
Then the electricity carrier and demand (time series) are added to the
energysystem. Finally, the energy system is optimised/solved via
meta_model.solve and the solver output is written to an .lp file.
"""

import os

from oemof import solph
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
meta_model = MetaModel()

house_1 = Location(name="house_1")
meta_model.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=35))

house_1.add(
    demands.Electricity(
        name="electricity demand",
        time_series=[0, 0.5],
    )
)

solph_representation = SolphModel(
    meta_model,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 02:00:00",
        "freq": "60min",
    },
)

solph_representation.build_solph_model()

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = solph.Results(solved_model)
flows = myresults["flow"]

label1 = ("input", "electricity demand", "house_1")
label2 = ("sink", "electricity demand", "house_1")
flow_electricity = flows[(str(label1), str(label2))]

print(flow_electricity)

units = get_flow_units(solph_representation)
flow_colours = get_energy_types(solph_representation)
solph_representation.graph(
    flow_results=flows, units=units, flow_colours=flow_colours
)
