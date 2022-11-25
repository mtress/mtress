from mtress import carriers, demands, Location, MetaModel, technologies

from mtress._helpers._visualization import generate_graph

"""
    Basic working 'electricity and heat' example which includes a location (house),
    electricity wise: an electricity carrier which acts as a electricity
    source/supply from the official grid (working price of 35 ct/kWh) as well as 
    a demand (consumer) with a demand time series.
    And heat wise: a heat carrier, a heat pump, an air heat exchanger as well as
    a heat demand time series.

    At first an energy system (here meta_model) is defined with a time series (index).
    Afterwards a location is defined and added to the energysystem. Then the 
    electricity carrier and electricity demand (time series) are added to the 
    energysystem. Furthermore a heat carrier is defined with specific temp-
    erature level(s) and a reference temperature. Then  a heat demand (time series)
    is added with a certain flow and return temperature. Lastly, a heat pump with
    a possible thermal power limit and an air heat exchanger with a certain air 
    temperature are added to the energy system.  
    
    Finally, the energy system is optimised/solved via meta_model.solve, a plot is
    created and the solver output is written to an .lp file.   
"""


energy_system = MetaModel(time_index={
    "start": "2021-07-10 00:00:00",
    "end": "2021-07-10 00:00:00",
    "freq": "60T",
})

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add_carrier(
    carriers.Electricity(costs={"working_price": 35, "demand_rate": 0})
)

house_1.add_demand(
    demands.Electricity(time_series=[9])
)

house_1.add_carrier(
    carriers.Heat(
        temperature_levels=[30],
        reference_temperature=20,
    )
)
house_1.add_demand(
    demands.FixedTemperatureHeat(
        flow_temperature=30,
        return_temperature=20,
        time_series=[50],
    )
)

house_1.add_component(
    technologies.HeatPump(thermal_power_limit=None)
)

house_1.add_component(
    technologies.AirHeatExchanger(air_temperatures=[3])
)

solved_model = energy_system.solve(solve_kwargs={"tee": True})

plot = generate_graph(solved_model.es)
plot.render(format="pdf")

solved_model.write('electricity_heat.lp',
                   io_options={'symbolic_solver_labels': True})
