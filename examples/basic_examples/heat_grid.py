"""
Basic example to represent the import of heat assuming the existance of a heat
network
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

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[10, 20, 30, 55],
    )
)
house_1.add(
    technologies.HeatGridInterconnection(
        maximum_working_temperature=30, minimum_working_temperature=20
    )
)
house_2 = Location(name="house_2")
energy_system.add_location(house_2)

house_2.add(
    carriers.HeatCarrier(
        temperature_levels=[10, 20, 30, 55],
    )
)

house_2.add(
    technologies.HeatGridInterconnection(
        maximum_working_temperature=30, minimum_working_temperature=20
    )
)
house_2.add(
    demands.FixedTemperatureHeating(
        name="space heating",
        min_flow_temperature=30,
        return_temperature=20,
        time_series=[50, 60],
    )
)

house_3 = Location(name="Heat Plant")
energy_system.add_location(house_3)

house_3.add(
    carriers.HeatCarrier(
        temperature_levels=[10, 20, 30, 55],
    )
)

house_3.add(
    technologies.HeatGridConnection(
        heat_network_temperature=30,
        maximum_working_temperature=30,
        minimum_working_temperature=20,
        grid_limit=1e4,
    )
)
house_3.add(
    technologies.HeatGridInterconnection(
        maximum_working_temperature=30, minimum_working_temperature=20
    )
)
solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 02:00:00",
        "freq": "60min",
    },
)

house_3.connect(
    connection=technologies.HeatGridInterconnection, destination=house_1
)
house_1.connect(
    connection=technologies.HeatGridInterconnection, destination=house_2
)

solph_representation.build_solph_model()

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

myresults = Results(solved_model)
flows = myresults["flow"]
units = get_flow_units(solph_representation)
flow_colours = get_energy_types(solph_representation)
solph_representation.graph(
    flow_results=flows, units=units, flow_colours=flow_colours
)
