"""Simple example to illustrate heat production from resistive heater"""

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

house_1.add(carriers.HeatCarrier(temperature_levels=[20, 30, 50]))
house_1.add(
    technologies.ResistiveHeater(
        name="Resistive_Heater",
        thermal_power_limit=None,
        maximum_temperature=50,
        minimum_temperature=20,
        efficiency=0.8,
    )
)
house_1.add(
    demands.FixedTemperatureHeating(
        name="heating",
        min_flow_temperature=50,
        return_temperature=20,
        time_series=[50, 50],
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

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = Results(solved_model)
flows = myresults["flow"]
units = get_flow_units(solph_representation)
flow_colours = get_energy_types(solph_representation)
solph_representation.graph(
    flow_results=flows, units=units, flow_colours=flow_colours
)
