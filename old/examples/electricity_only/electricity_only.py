"""
Basic working 'electricity only' example.

Basic working 'electricity only' example which includes a location (house),
an electricity carrier which acts as a electricity source/supply from the
official grid (working price of 35 ct/kWh) as well as a demand (consumer)
with a demand time series.

At first an energy system is defined with a time series (index).
Afterwards a location is defined and added to the energy system.
Then the electricity carrier and demand (time series) are added to the
energy system.
"""

from oemof import solph
from mtress import (
    Location,
    EnergySystem,
    demands,
    technologies,
)

import os

os.chdir(os.path.dirname(__file__))

energy_system = EnergySystem(
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 02:00:00",
        "freq": "60min",
    },
)

house_1 = Location(label="house_1")
energy_system.add(house_1)

house_1.subnode(
    technologies.ElectricityGridConnection,
    "EGC",
    working_rate=35,
)

house_1.subnode(
    demands.Electricity,
    "electricity demand",
    time_series=[0, 0.5],
)

energy_system.establish_interconnections()

energy_system.graph()

model = solph.Model(energy_system)

energy_system.add_constraints(model)

model.write("electricity_only.lp", io_options={"symbolic_solver_labels": True})

myresults = model.solve(solve_kwargs={"tee": True})

flows = myresults["flow"]

energy_system.graph(flow_results=flows, path="model_results.png")

label1 = str(("input", "electricity demand", "house_1"))
label2 = str(("sink", "electricity demand", "house_1"))
flow_electricity = flows[label1, label2]

print(flow_electricity)
