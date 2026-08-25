"""
This example shows how to introduce fixed losses per hour independent of
storage content and of nominal storage capacity.
"""

import os

import matplotlib.pyplot as plt
from oemof.solph import Model

from mtress import EnergySystem, Location, carriers, components, demands
from mtress._helpers._visualization import graph_graphviz

os.chdir(os.path.dirname(__file__))

energy_system = EnergySystem(
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 02:00:00",
        "freq": "60min",
    },
)

house_1 = Location(label="house_1")
energy_system.add(house_1)

house_1.subnode(
    carriers.ElectricityCarrier,
    local_name="EC",
)

house_1.subnode(
    components.ElectricityGridConnection,
    "EGC",
    working_rate=35,
)

battery = components.BatteryStorage(
    "Battery",
    nominal_capacity=2e3,  # Wh
    charging_C_Rate=1,
    discharging_C_Rate=1,
    charging_efficiency=1,
    initial_soc=0.1,
    loss_rate=0,
    fixed_losses_absolute=[1e1, 1e1],
)

house_1.subnode(
    components.BatteryStorage,
    "Battery",
    nominal_capacity=2e3,  # Wh
    charging_C_Rate=1,
    discharging_C_Rate=1,
    charging_efficiency=1,
    initial_soc=0.1,
    loss_rate=0,
    fixed_losses_absolute=[1e1, 1e1],
)

house_1.subnode(
    demands.ElectricityDemand,
    "electricity_demand",
    time_series=[20, 40],
)

energy_system.establish_interconnections()

graph_graphviz(
    energy_system.nodes,
    path="electricity_battery.png",
)

model = Model(energy_system)

myresults = model.solve()

flows = myresults["flow"]

graph_graphviz(
    energy_system.nodes,
    flows=flows,
    path="electricity_battery_results.png",
)

label1 = ("distribution", "EC", "house_1")
label2 = ("i/o", "Battery", "house_1")
charging_power = flows[(str(label1), str(label2))]

print(charging_power)

plt.figure(figsize=(10, 5))
plt.plot(charging_power.index, charging_power)
plt.xticks(
    charging_power.index,
    [x.strftime("%H:00") for x in charging_power.index],
)
plt.ylabel("Power (W)")
plt.show()
