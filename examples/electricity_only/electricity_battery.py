"""
This example shows how to introduce fixed losses per hour independent of
storage content and of nominal storage capacity.
"""

import os

import matplotlib.pyplot as plt
from oemof.solph.processing import results
from oemof.solph.processing import meta_results
from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    technologies,
    demands
)
from mtress._helpers import get_flows

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(
    technologies.ElectricityGridConnection(
        working_rate=1,
        # revenue=2,
        # grid_import_limit=1000,
        # grid_export_limit=1000,
        )
    )

battery = technologies.BatteryStorage(
    name="Battery",
    nominal_capacity=2e3,  # Wh
    charging_C_Rate=1,
    discharging_C_Rate=1,
    charging_efficiency=1,
    initial_soc=0.1,
    loss_rate=0,
    fixed_losses_absolute=[1e1, 1e1]
)

house_1.add(battery)

house_1.add(
    demands.Electricity(
        name="electricity_demand",
        time_series=[20, 40],
    )
)

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 10:00:00",
        "end": "2021-07-10 12:00:00",
        "freq": "60min",
        "tz": "Europe/Berlin",
    },
)

solph_representation.build_solph_model()

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
mr = meta_results(solved_model)
myresults = results(solved_model)
flows = get_flows(myresults)

charging_power = flows[
    ("house_1", "ElectricityCarrier", "distribution"),
    ("house_1", "Battery", "Battery_Storage"),
]

plt.figure(figsize=(10, 5))
plt.plot(charging_power.index[:-1], charging_power[:-1])
plt.xticks(
    charging_power.index[:-1],
    [x.strftime("%H:00") for x in charging_power.index[:-1]],
)
plt.ylabel("Power (W)")
plt.show()

solph_representation.graph(flow_results=flows)
