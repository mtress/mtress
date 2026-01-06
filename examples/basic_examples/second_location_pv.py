"""
Basic working 'electricity' example.
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

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=35))

weather = {
    "ghi": "FILE:../weather.csv:ghi",
    "dhi": "FILE:../weather.csv:dhi",
    "wind_speed": "FILE:../weather.csv:wind_speed",
    "temp_air": "FILE:../weather.csv:temp_air",
    "temp_dew": "FILE:../weather.csv:temp_dew",
    "pressure": "FILE:../weather.csv:pressure",
}


house_1.add(
    technologies.RenewableElectricitySource(
        "pv0",
        nominal_power=10000,
        specific_generation="FILE:../input_file.csv:pv",
        fixed=False,
    )
)

house_2 = Location(name="house_2")
energy_system.add_location(house_2)
house_2.add(carriers.ElectricityCarrier())
house_2.add(technologies.ElectricityGridConnection(working_rate=50))
house_2.add(demands.Electricity(name="demand0", time_series=10))

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-07-10 00:00:00",
        "freq": "60min",
        "periods": 10,
        "tz": "Europe/Berlin",
    },
)

# Far from optimal, but currently only works on the existing solph model
house_1.connect(
    connection=technologies.ElectricityGridConnection, destination=house_2
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

solved_model.write(
    "second_location_pv.lp", io_options={"symbolic_solver_labels": True}
)
