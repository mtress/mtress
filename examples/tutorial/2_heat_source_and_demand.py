import os
from oemof.solph import Results
from mtress import (
    EnergySystem,
    Location,
    carriers,
    demands,
    technologies,
)

from mtress._helpers import get_flow_units, get_energy_types

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

# Add carriers
house_1.subnode(
    carriers.HeatCarrier,
    local_name="HC",
    temperature_levels=[5, 10, 20, 30, 40],
)

# Add technologies
house_1.subnode(
    technologies.HeatSink,
    local_name="air_HE",
    reservoir_temperature=15,
    maximum_working_temperature=40,
    minimum_working_temperature=5,
    nominal_power=1e4,
)

# Add demands
house_1.subnode(
    demands.FixedTemperatureHeating,
    local_name="Heating_demand",
    min_flow_temperature=20,
    return_temperature=10,
    time_series=[25, 25],
)

house_1.subnode(
    demands.FixedTemperatureCooling,
    local_name="Cooling_demand",
    return_temperature=30,
    max_flow_temperature=10,
    time_series=[50, 50],
)

energy_system.establish_interconnections()

# model = Model(energy_system)

# myresults = model.solve()

graph_graphviz(
    energy_system.nodes,
    path="2_heat_source_and_demand_model.png",
)
