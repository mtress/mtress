"""
Basic working 'electricity' example.
"""

import os
import pandas as pd
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
from mtress.physics import HYDROGEN
from mtress.technologies import PEM_ELECTROLYSER

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(
    technologies.ElectricityGridConnection(working_rate=None, revenue=0.0001)
)

house_1.add(
    technologies.RenewableElectricitySource(
        "pv0",
        nominal_power=8000,
        specific_generation="FILE:../input_file.csv:pv",
        fixed=False,
    )
)

house_1.add(
    technologies.Electrolyser(
        name="Ely",
        nominal_power=1000,
        template=PEM_ELECTROLYSER,
        hydrogen_output_pressure=60,
    )
)

house_1.add(carriers.GasCarrier(gases={HYDROGEN: [60, 30]}))
house_1.add(carriers.HeatCarrier(temperature_levels=[20, 50]))
house_1.add(
    technologies.GasGridConnection(
        name="H2-Grid",
        working_rate=None,
        gas_type=HYDROGEN,
        grid_pressure=30,
        revenue=7.8,
    )
)
house_1.add(
    demands.FixedTemperatureHeating(
        name="heating",
        time_series=100,
        min_flow_temperature=50,
        return_temperature=20,
    )
)
house_2 = Location(name="house_2")
energy_system.add_location(house_2)
house_2.add(carriers.ElectricityCarrier())
house_2.add(
    technologies.ElectricityGridConnection(working_rate=0.25, revenue=None)
)
house_2.add(demands.Electricity(name="demand0", time_series=500))

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-07-10 10:00:00",
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

# solved_model.write(
#     "connecting_location.lp", io_options={"symbolic_solver_labels": True}
# )
