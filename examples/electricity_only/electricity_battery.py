"""
This example shows how to introduce fixed losses per hour independent of
storage content and of nominal storage capacity.
"""

import os

import matplotlib.pyplot as plt
from oemof.solph.processing import results

from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    technologies,
)
from mtress._helpers import get_flows
from mtress._helpers._visualization import render_series

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=0))

battery = technologies.BatteryStorage(
    name="Battery",
    nominal_capacity=2e3,  # Wh
    charging_C_Rate=0.5,
    discharging_C_Rate=0,
    charging_efficiency=1,
    initial_soc=0.1,
    loss_rate=0,
    fixed_losses_absolute=[1e3, 1e3, 1e3],
)

house_1.add(battery)

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 10:00:00",
        "end": "2021-07-10 13:00:00",
        "freq": "60T",
        "tz": "Europe/Berlin",
    },
)

solph_representation.build_solph_model()

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
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

plot = solph_representation.graph(
    detail=True, flow_results=flows, flow_color=None
)
plot.render(outfile="electricity_battery_results.png")
