import os

from oemof.solph.processing import results

from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
from mtress._helpers import get_flows

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[5, 10, 20, 30, 40],
        reference_temperature=0,
    )
)

import pandas as pd

t_amb = pd.Series([10, 15, 18, 20, 21, 22, 25])
# "FILE:../input_file.csv:temp_air"

house_1.add(
    technologies.HeatExchanger2(
        name="ahe",
        reservoir_temperature=t_amb,
        maximum_working_temperature=40,
        minimum_working_temperature=0,
    )
)

house_1.add(
    demands.FixedTemperatureHeatCool(
        name="Heating_demand",
        flow_temperature=30,
        return_temperature=20,
        time_series=[50, 50, 50, 50, 50, 50, 50],
    )
)

house_1.add(
    demands.FixedTemperatureHeatCool(
        name="Cooling_demand",
        flow_temperature=40,
        return_temperature=30,
        time_series=[50, 50, 50, 50, 50, 50, 50],
        sink=False,
    )
)

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 07:00:00",
        "freq": "60T",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="heat_exchanger.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = results(solved_model)
flows = get_flows(myresults)
