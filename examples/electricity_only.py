

from mtress import carriers, demands, Location, MetaModel

meta_model = MetaModel(time_index={
    "start": "2021-07-10 00:00:00",
    "end": "2021-07-10 02:00:00",
    "freq": "60T",
})

house_1 = Location(name="house_1")
meta_model.add_location(house_1)

house_1.add_carrier(
    carriers.Electricity(costs={"working_price": 35, "demand_rate": 0}))

house_1.add_demand(
    demands.Electricity(time_series=[0, 0.5, 9]))

solved_model = meta_model.solve(solve_kwargs={"tee": True})
solved_model.write('electricity_only.lp', io_options={'symbolic_solver_labels': True})
