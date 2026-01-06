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
house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[
            10,
            20,
            30,
        ],  # Introduce relevant temperature levels
    )
)

# Add technologies
house_1.add(
    technologies.HeatSource(
        name="air_HE",
        reservoir_temperature=25,  # any possible source
        maximum_working_temperature=40,
        minimum_working_temperature=10,
        nominal_power=1e4,
    )
)

# Add demands
house_1.add(
    demands.FixedTemperatureHeating(
        name="heat_demand",
        min_flow_temperature=20,
        return_temperature=10,
        time_series=[50, 50],
    )
)

# Solve the system
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
    path="1_heat_exchanger_model.png",
)
