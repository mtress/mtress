"""
Basic working 'EV' example.
"""

import os

# from oemof import solph
import math
import matplotlib.pyplot as plt
from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress._helpers import get_flows
from oemof.solph.processing import results
from oemof.solph.processing import meta_results
# from pandas import Series

nominal_electricity_price = 0.1/1000 # 0.1 EUR/kWh = 0.1/1000 EUR/Wh
number_intervals = 24
distance_travelled = [0 for i in range(number_intervals)]
distance_travelled[8] = 50 # morning commute
distance_travelled[17] = 50 # afternoon commute

os.chdir(os.path.dirname(__file__))
meta_model = MetaModel()

house_1 = Location(name="house_1")
meta_model.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(
    technologies.ElectricityGridConnection(
        working_rate=[
            nominal_electricity_price
            for i in range(number_intervals)
            ],
        # revenue=[
        #     35+(50 if i > 9 and i < 15 else 0)
        #     for i in range(number_intervals)
        #     ],
        grid_import_limit=5e3, # 5 kWh per hour
        # grid_export_limit=10e3, # 10 kWh per hour
        )
    )

house_1.add(
    technologies.ElectricVehicle(
        name="ev",
        template=technologies.GenericSegmentB_EV,
        distance_travelled=distance_travelled
        )
    )

house_1.add(
    demands.Electricity(
        name="electricity demand",
        time_series=[0 for i in range(number_intervals)],
    )
)

solph_representation = SolphModel(
    meta_model,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-11 00:00:00",
        "freq": "60min",
    },
)

solph_representation.build_solph_model()

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

mr = meta_results(solved_model)
myresults = results(solved_model)
flows = get_flows(myresults)
round_trip_efficiency = (
    technologies.GenericSegmentB_EV.charging_efficiency*
    technologies.GenericSegmentB_EV.discharging_efficiency
    )
energy_used = (
    sum(distance_travelled)* # km
    technologies.GenericSegmentB_EV.consumption_per_distance/ # kWh/km
    round_trip_efficiency
    )
expected_result = nominal_electricity_price*energy_used
assert math.isclose(expected_result, mr["objective"], abs_tol=1e-3)
charging_power = flows[
    ("house_1", "ElectricityCarrier", "distribution"),
    ("house_1", "ev", "EV"),
]
discharging_power = flows[
    ("house_1", "ev", "EV"),
    ("house_1", "ElectricityCarrier", "distribution"),
]

plt.figure(figsize=(10, 5))
plt.plot(charging_power.index[:-1], charging_power[:-1])
plt.xticks(
    charging_power.index[:-1],
    [x.strftime("%H:00") for x in charging_power.index[:-1]],
)
plt.ylabel("Power (W)")
plt.show()

plt.figure(figsize=(10, 5))
plt.plot(discharging_power.index[:-1], discharging_power[:-1])
plt.xticks(
    discharging_power.index[:-1],
    [x.strftime("%H:00") for x in discharging_power.index[:-1]],
)
plt.ylabel("Power (W)")
plt.show()

solph_representation.graph(flow_results=flows)
