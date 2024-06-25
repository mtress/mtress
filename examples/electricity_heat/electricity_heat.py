"""
Basic working 'electricity and heat' example.

Basic working 'electricity and heat' example which includes a location (house),
electricity wise: an electricity carrier which acts as a electricity
source/supply from the official grid (working price of 0.035 ct/Wh) as well as
a demand (consumer) with a demand time series.
And heat wise: a heat carrier, a heat pump, an heat exchanger as well as
a heat demand time series.

At first an energy system (here meta_model) is defined with a time series (index).
Afterwards a location is defined and added to the energysystem. Then the
electricity carrier and electricity demand (time series) are added to the
energysystem. Furthermore a heat carrier is defined with specific temp-
erature level(s) and a reference temperature. Then  a heat demand (time series)
is added with a certain flow and return temperature. Lastly, a heat pump with
a possible thermal power limit and heat exchanger with a certain air
temperature are added to the energy system.

Finally, the energy system is optimised/solved via meta_model.solve, a plot is
created and the solver output is written to an .lp file.
"""

import os

from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.Electricity())
house_1.add(technologies.ElectricityGridConnection(working_rate=0.035))

house_1.add(
    demands.Electricity(
        name="electricity demand",
        time_series=[9, 13],
    )
)

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[10, 20, 30, 40, 55],
        reference_temperature=0,
    )
)
house_1.add(
    demands.FixedTemperatureHeating(
        name="space_heating",
        min_flow_temperature=30,
        return_temperature=20,
        time_series=[50, 60],
    )
)

house_1.add(
    technologies.HeatPump(
        name="HeatPump",
        thermal_power_limit=None,
        max_temp_primary=18,
        min_temp_primary=10,
        max_temp_secondary=40,
        min_temp_secondary=30,
    )
)

house_1.add(
    technologies.HeatSource(
        name="Air_HE",
        reservoir_temperature=20,
        maximum_working_temperature=40,
        minimum_working_temperature=10,
        nominal_power=1e4,
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
plot.render(outfile="electricity_heat_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="electricity_heat_simple.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

solved_model.write("electricity_heat.lp", io_options={"symbolic_solver_labels": True})
