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

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

# Add carrier
house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=35))

house_1.add(carriers.HeatCarrier(temperature_levels=[5, 10, 20, 30, 40]))

# Add technologies
house_1.add(
    technologies.HeatExchanger(
        name="Air_HE",
        reservoir_temperature=20,
        maximum_working_temperature=40,
        minimum_working_temperature=5,
        nominal_power=1e4,
    )
)

house_1.add(
    technologies.HeatPump(
        name="HeatPump",
        thermal_power_limit=None,
        max_temp_primary=10,
        min_temp_primary=5,
        max_temp_secondary=40,
        min_temp_secondary=30,
    )
)

# Add demands
house_1.add(
    demands.FixedTemperatureCooling(
        name="Cooling_demand",
        max_flow_temperature=5,
        return_temperature=10,
        time_series=[50, 50, 40, 25],
    )
)

house_1.add(
    demands.FixedTemperatureHeating(
        name="Heating_demand",
        min_flow_temperature=40,
        return_temperature=30,
        time_series=[50, 50, 30, 40],
    )
)


solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 04:00:00",
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
    flow_results=flows,
    units=units,
    flow_colours=flow_colours,
    path="3_heat_pump_model.png",
)
