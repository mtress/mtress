import os
from oemof.solph import Model

from mtress import (
    EnergySystem,
    Location,
    carriers,
    demands,
    technologies,
)

from mtress._helpers._visualization import graph_graphviz

os.chdir(os.path.dirname(__file__))

energy_system = EnergySystem(
    timeindex={
        "start": "2022-01-10 00:00:00",
        "end": "2022-01-10 02:00:00",
        "freq": "60min",
    },
)

house_1 = Location(label="house_1")
energy_system.add(house_1)

house_1.subnode(
    carriers.HeatCarrier,
    local_name="HC",
    temperature_levels=[2, 5, 10, 11, [19,21], 20, [30, 30.5]],
)


# Add technologies
house_1.subnode(
    technologies.HeatSource,
    local_name="air_HE",
    reservoir_temperature=[45,35],  # any possible source
    maximum_working_temperature=40,
    minimum_working_temperature=5,
    minimum_delta_reservoir=5,
    nominal_power=1e4,
)

# Add demands
hd = house_1.subnode(
    demands.FixedTemperatureHeating,
    local_name="heat_demand",
    min_flow_temperature=20,
    return_temperature=10,
    time_series=[50, 50],
)

energy_system.establish_interconnections()

# model = Model(energy_system)

# myresults = model.solve()

graph_graphviz(
    energy_system.nodes,
    path="1_heat_exchanger_model.png",
)
