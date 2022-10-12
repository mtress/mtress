

from mtress import carriers, demands, Location, MetaModel, technologies

meta_model = MetaModel(time_index={
    "start": "2021-07-10 00:00:00",
    "end": "2021-07-10 02:00:00",
    "freq": "60T",
})

house_1 = Location(meta_model=meta_model, name="house_1")

carriers.Electricity(location=house_1, costs={"working_price": 35, "demand_rate": 0})

demands.Electricity(location=house_1, time_series=[0, 0.5, 9])

carriers.Heat(
    location=house_1,
    temperature_levels=[30],
    reference_temperature=20,
)

demands.SpaceHeating(location=house_1, time_series=[0, 8, 0.25])

technologies.FixedTemperatureHeater(
    location=house_1,
    flow_temperature=30,
    return_temperature=20,
)

hp = technologies.HeatPump(location=house_1)

technologies.AirHeatExchanger(location=house_1, air_temperatures=[10, -0.5, 13])

hp.add_interconnections()

solved_model = meta_model.solve(solve_kwargs={"tee": True})
solved_model.write('electricity_heat.lp', io_options={'symbolic_solver_labels': True})
