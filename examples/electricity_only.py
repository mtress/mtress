

from mtress import carriers, demands, Location, MetaModel

meta_model = MetaModel(time_index={
    "start": "2021-07-10 00:00:00",
    "end": "2021-07-10 02:00:00",
    "freq": "60T",
})

house_1 = Location(meta_model=meta_model, name="house_1")

carriers.Electricity(location=house_1, costs={"working_price": 35, "demand_rate": 0})

demands.Electricity(location=house_1, time_series=[0, 0.5, 9])

solved_model = meta_model.solve(solve_kwargs={"tee": True})
solved_model.write('electricity_only.lp', io_options={'symbolic_solver_labels': True})
