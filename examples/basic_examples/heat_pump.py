"""Simple example to illustrate heat production from resistive heater"""

import os

from oemof.solph.processing import results

from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
from mtress._helpers import get_flows

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.Electricity())
house_1.add(technologies.ElectricityGridConnection(working_rate=35))

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[-5, 0, 5, 15, 20, 30, 40],
        reference_temperature=-10,
    )
)

house_1.add(
    technologies.AirHeatExchanger(
        name="ahe", air_temperatures=20, minimum_temperature=15
    )
)

house_1.add(
    technologies.HeatPump(
        name="HeatPump",
        thermal_power_limit=None,
        max_temp_primary=20,
        min_temp_primary=15,
        max_temp_secondary=50,
        min_temp_secondary=30,
    )
)

house_1.add(
    technologies.LayeredHeatStorage(
        name="hst1",
        diameter=3,
        volume=10,
        power_limit=None,
        ambient_temperature=20,
        u_value=None,
        max_temperature=50,
        min_temperature=20,
    )
)
house_1.add(
    technologies.LayeredHeatStorage(
        name="hst2",
        diameter=3,
        volume=10,
        power_limit=None,
        ambient_temperature=20,
        u_value=None,
        max_temperature=15,
        min_temperature=0,
    )
)

house_1.add(
    demands.FixedTemperatureHeating(
        name="heating",
        min_flow_temperature=15,
        return_temperature=0,
        time_series=[50, 50],
    )
)

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 02:00:00",
        "freq": "60T",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="heat_pump_detail.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = results(solved_model)
flows = get_flows(myresults)

solved_model.write("heat.lp", io_options={"symbolic_solver_labels": True})
