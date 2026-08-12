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

import os

from oemof.solph import Model

from mtress import EnergySystem, Location, carriers, demands, components
from mtress._helpers._visualization import graph_graphviz

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
    carriers.ElectricityCarrier,
    local_name="EC",
)

house_1.subnode(
    components.ElectricityGridConnection,
    "EGC",
    working_rate=35,
)

house_1.subnode(
    demands.Electricity,
    "electricity demand 1",
    time_series=[0, 0.5],
)


energy_system.establish_interconnections()

graph_graphviz(
    energy_system.nodes,
    path="electricity_only.png",
)

model = Model(energy_system)

myresults = model.solve()

flows = myresults["flow"]

graph_graphviz(
    energy_system.nodes,
    flows=flows,
    path="electricity_only_results.png",
)
