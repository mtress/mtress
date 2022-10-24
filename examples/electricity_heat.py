from mtress import carriers, demands, Location, MetaModel, technologies

from mtress._helpers._visualization import generate_graph

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
