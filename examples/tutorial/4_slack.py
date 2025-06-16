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

from oemof.solph.processing import results

from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress._helpers import get_flows

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
myresults = results(solved_model)
flows = get_flows(myresults)

# indicate usage of SlackNode with a rainbow-colored scheme
flow_color = {
    ("house_1", "SlackNode", "missing_energy"): {
        (
            "house_1",
            "ElectricityCarrier",
            "distribution",
        ): "rainbow",
        ("house_1", "HeatCarrier", "T_5"): "rainbow",
        ("house_1", "HeatCarrier", "T_10"): "rainbow",
        ("house_1", "HeatCarrier", "T_20"): "rainbow",
        ("house_1", "HeatCarrier", "T_30"): "rainbow",
        ("house_1", "HeatCarrier", "T_40"): "rainbow",
    },
    ("house_1", "ElectricityCarrier", "distribution"): {
        ("house_1", "SlackNode", "excess_energy"): "rainbow"
    },
    ("house_1", "HeatCarrier", "T_5"): {
        ("house_1", "SlackNode", "excess_energy"): "rainbow"
    },
    ("house_1", "HeatCarrier", "T_10"): {
        ("house_1", "SlackNode", "excess_energy"): "rainbow"
    },
    ("house_1", "HeatCarrier", "T_20"): {
        ("house_1", "SlackNode", "excess_energy"): "rainbow"
    },
    ("house_1", "HeatCarrier", "T_30"): {
        ("house_1", "SlackNode", "excess_energy"): "rainbow"
    },
    ("house_1", "HeatCarrier", "T_40"): {
        ("house_1", "SlackNode", "excess_energy"): "rainbow"
    },
}

solph_representation.graph(
    flow_results=flows,
    flow_color=flow_color,
    path="4_slack_model.png",
)
