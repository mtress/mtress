"""
Basic working 'heat' example to ilustrate the use of a boiler.
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
from mtress.physics import NATURAL_GAS

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

# Add grid connections
house_1.add(
    technologies.GasGridConnection(
        name="NG_Grid",
        gas_type=NATURAL_GAS,
        grid_pressure=10,
        working_rate=15,
    )
)

# Add carriers
house_1.add(carriers.GasCarrier(gases={NATURAL_GAS: [10]}))

house_1.add(carriers.HeatCarrier(temperature_levels=[20, 30, 50]))

# Add demands
house_1.add(
    demands.FixedTemperatureHeating(
        name="hot water",
        min_flow_temperature=50,
        return_temperature=20,
        time_series=[10000, 2000],
    )
)

# Add technologies
house_1.add(
    technologies.GasBoiler(
        name="Boiler",
        gas_type=NATURAL_GAS,
        maximum_temperature=55,
        minimum_temperature=20,
        thermal_power_limit=50000,  #  W
        efficiency=0.85,
        input_pressure=10,
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

solph_representation.build_solph_model()

solved_model = solph_representation.solve(solve_kwargs={"tee": False})
myresults = Results(solved_model)
flows = myresults["flow"]
units = get_flow_units(solph_representation)
flow_colours = get_energy_types(solph_representation)
solph_representation.graph(
    flow_results=flows, units=units, flow_colours=flow_colours
)
