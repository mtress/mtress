"""
Basic working 'electricity' example.
"""

import os

import pandas as pd
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
from mtress._helpers._visualization import render_series

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=35))

house_1.add(demands.Electricity(name="demand0", time_series=10))

house_1.add(
    technologies.RenewableElectricitySource(
        "pv0",
        nominal_power=8000,
        specific_generation="FILE:../input_file.csv:pv",
        fixed=False,
    )
)

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-07-10 00:00:00",
        "freq": "60min",
        "periods": 10,
        "tz": "Europe/Berlin",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="electricity_pv_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="electricity_pv_simple.png")


solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = results(solved_model)
flows = get_flows(myresults)

plot = solph_representation.graph(
    detail=True, flow_results=flows, flow_color=None
)
plot.render(outfile="electricity_pv_results.png")

plot_series = solph_representation.graph_series(
    flow_results=flows, step=pd.Timedelta("240min")
)
render_series(plot_series, "electricity_pv_series", 1000)

solved_model.write(
    "electricity_pv.lp", io_options={"symbolic_solver_labels": True}
)
