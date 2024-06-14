import os
import pandas as pd
from oemof.solph.processing import results

from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
from mtress._helpers import get_flows

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

# Add carriers
house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[5, 10, 20, 30, 40],
        reference_temperature=0,
    )
)

# Add technologies
house_1.add(
    technologies.HeatExchanger2(
        name="air_HE",
        reservoir_temperature=25,
        maximum_working_temperature=40,
        minimum_working_temperature=0,
    )
)

# Add demands

house_1.add(
    demands.FixedTemperatureHeatCool(
        name="Heating_demand",
        flow_temperature=20,
        return_temperature=10,
        time_series=[50, 50],
    )
)

house_1.add(
    demands.FixedTemperatureHeatCool(
        name="Cooling_demand",
        flow_temperature=10,
        return_temperature=5,
        time_series=[50, 50],
        sink=False,
    )
)

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-01-10 00:00:00",
        "end": "2022-01-10 02:00:00",
        "freq": "60T",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="heat_source_and_demand_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="heat_source_and_demand_simple.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = results(solved_model)
flows = get_flows(myresults)

solved_model.write("heat.lp", io_options={"symbolic_solver_labels": True})
