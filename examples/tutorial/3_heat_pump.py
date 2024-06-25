import os
import pandas as pd
from oemof.solph.processing import results

from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
from mtress._helpers import get_flows

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

# Add carrier
house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=35))

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[5, 10, 20, 30, 40],
        reference_temperature=0,
    )
)

# Add technologies
house_1.add(
    technologies.HeatExchanger(
        name="Air_HE",
        reservoir_temperature=20,
        maximum_working_temperature=40,
        minimum_working_temperature=10,
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
        time_series=[50, 50],
    )
)

house_1.add(
    demands.FixedTemperatureHeating(
        name="Heating_demand",
        min_flow_temperature=30,
        return_temperature=20,
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
plot.render(outfile="heat_pump_cooling_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="heat_pump_cooling_simple.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = results(solved_model)
flows = get_flows(myresults)

plot = solph_representation.graph(detail=True, flow_results=flows)
plot.render(outfile="heat_pump_cooling_results.png")
