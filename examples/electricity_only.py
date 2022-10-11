

from mtress import carriers, demands, Location, MetaModel, technologies

meta_model = MetaModel(time_index={
    "start": "2021-07-10 00:00:00",
    "end": "2021-07-10 05:00:00",
    "freq": "60T",
})

house_1 = Location(meta_model=meta_model, name="house_1")

carrier_el = carriers.Electricity(location=house_1, costs={"working_price": 35, "demand_rate": 0})

demand_el = demands.Electricity(location=house_1, time_series=[0, 1, 2, 3, 2, 1, 0])

meta_model.solve()

