"""
This example shows how to use the SlackNode technology.
First a basic energy system is created.
Next, the SlackNode technology is created with different
    penalties per energy carrier.
Lastly, after the model is build and solved,
    flows from and to the SlackNode are strongly highlighted
    in the results plot.
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

# Add carriers
house_1.add(carriers.ElectricityCarrier())
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

house_1.add(
    technologies.RenewableElectricitySource(
        name="pv",
        nominal_power=1.0,
        specific_generation=[5, 10],
    )
)

# Add demands
house_1.add(
    demands.Electricity(name="Electricity_demand", time_series=[10, 15])
)
house_1.add(
    demands.FixedTemperatureHeating(
        name="Heating_demand",
        min_flow_temperature=20,
        return_temperature=10,
        time_series=[25, 35],
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

# Add slack
house_1.add(technologies.SlackNode())

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-01-10 00:00:00",
        "end": "2022-01-10 02:00:00",
        "freq": "60min",
    },
)

solph_representation.build_solph_model()

solved_model = solph_representation.solve(solve_kwargs={"tee": False})
myresults = Results(solved_model)
flows = myresults["flow"]
units = get_flow_units(solph_representation)
flow_colours = get_energy_types(solph_representation)

# custom colour scheme
colour_scheme = {
    0: "black",  # Undefined
    1: "orange",  # Electricity
    2: "maroon",  # Heat
    3: "steelblue",  # Gas
    4: "rainbow",  # Slack
}

# indicate usage of SlackNode with a rainbow-coloured scheme
# (overwrite default flow colours)
slack_node_missing = solph_representation.energy_system._nodes[
    ("missing_energy", "SlackNode", "house_1")
]
slack_node_excess = solph_representation.energy_system._nodes[
    ("excess_energy", "SlackNode", "house_1")
]
for x in slack_node_missing.outputs.keys():
    flow_colours[(slack_node_missing, x)] = 4  # rainbow
for x in slack_node_excess.inputs.keys():
    flow_colours[(x, slack_node_excess)] = 4  # rainbow

solph_representation.graph(
    flow_results=flows,
    units=units,
    flow_colours=flow_colours,
    colour_scheme=colour_scheme,
    path="4_slack_model.png",
)
