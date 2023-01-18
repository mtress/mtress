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

from mtress import Location, MetaModel, SolphModel, carriers, demands

meta_model = MetaModel()

house_1 = Location(name="house_1")
meta_model.add_location(house_1)

house_1.add_carrier(carriers.Electricity(working_rate=35, demand_rate=0))

house_1.add_demand(demands.Electricity(time_series=[0, 0.5, 9]))

solph_representation = SolphModel(
    meta_model,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 02:00:00",
        "freq": "60T",
    },
)

solph_representation.build_solph_energy_system()
solph_representation.build_solph_model()

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

solved_model.write("electricity_only.lp", io_options={"symbolic_solver_labels": True})
