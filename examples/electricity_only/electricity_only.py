"""
Basic working 'electricity only' example.

Basic working 'electricity only' example which includes a location (house),
an electricity carrier which acts as a electricity source/supply from the 
official grid (working price of 35 ct/kWh) as well as a demand (consumer)
with a demand time series.

At first an energy system (here meta_model) is defined with a time series (index).
Afterwards a location is defined and added to the energysystem. Then the 
electricity carrier and demand (time series) are added to the energysystem. 
Finally, the energy system is optimised/solved via meta_model.solve and the 
solver output is written to an .lp file.   
"""

import os
from oemof import solph


from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
from mtress._helpers import get_flows

os.chdir(os.path.dirname(__file__))
meta_model = MetaModel()

house_1 = Location(name="house_1")
meta_model.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=35))

house_1.add(
    demands.Electricity(
        name="electricity demand",
        time_series=[0, 0.5],
    )
)

solph_representation = SolphModel(
    meta_model,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 02:00:00",
        "freq": "60T",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="electricity_only_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="electricity_only_simple.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

solved_model.write("electricity_only.lp", io_options={"symbolic_solver_labels": True})

myresults = solph.processing.results(solved_model)
flows = get_flows(myresults)

print(
    flows[
        ("house_1", "electricity demand", "input"),
        ("house_1", "electricity demand", "sink"),
    ]
)
