"""
Basic working 'electricity' example.
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

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = results(solved_model)
flows = get_flows(myresults)

solved_model.write(
    "electricity_pv.lp", io_options={"symbolic_solver_labels": True}
)

solph_representation.graph(flow_results=flows)
