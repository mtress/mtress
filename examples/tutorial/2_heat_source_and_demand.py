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

# Add carriers
house_1.add(carriers.HeatCarrier(temperature_levels=[5, 10, 20, 30, 40]))

# Add technologies
house_1.add(
    technologies.HeatSink(
        name="air_HE",
        reservoir_temperature=15,
        maximum_working_temperature=40,
        minimum_working_temperature=5,
        nominal_power=1e4,
    )
)

# Add demands
house_1.add(
    demands.FixedTemperatureHeating(
        name="Heating_demand",
        min_flow_temperature=20,
        return_temperature=10,
        time_series=[25, 25],
    )
)

house_1.add(
    demands.FixedTemperatureCooling(
        name="Cooling_demand",
        return_temperature=30,
        max_flow_temperature=10,
        time_series=[50, 50],
    )
)


house_2 = Location(name="house_2")
energy_system.add_location(house_2)

# Add carriers
house_2.add(carriers.HeatCarrier(temperature_levels=[5, 10, 20, 30, 40]))

# Add technologies
house_2.add(
    technologies.HeatSink(
        name="air_HE",
        reservoir_temperature=15,
        maximum_working_temperature=40,
        minimum_working_temperature=5,
        nominal_power=1e4,
    )
)

# Add demands
house_2.add(
    demands.FixedTemperatureHeating(
        name="Heating_demand",
        min_flow_temperature=20,
        return_temperature=10,
        time_series=[25, 25],
    )
)

house_2.add(
    demands.FixedTemperatureCooling(
        name="Cooling_demand",
        return_temperature=30,
        max_flow_temperature=10,
        time_series=[50, 50],
    )
)

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-01-10 00:00:00",
        "end": "2022-01-10 02:00:00",
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
    path="2_heat_source_and_demand_model.png",
)
