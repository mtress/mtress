"""
Basic working 'electricity' example.
"""
from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.Electricity(working_rate=35, demand_rate=0))

house_1.add(demands.Electricity(name="demand0", time_series=10))

weather = {
    "ghi": "FILE:mtress/examples/weather.csv:ghi",
    "dhi": "FILE:mtress/examples/weather.csv:dhi",
    "wind_speed": "FILE:mtress/examples/weather.csv:wind_speed",
    "temp_air": "FILE:mtress/examples/weather.csv:temp_air",
    "temp_dew": "FILE:mtress/examples/weather.csv:temp_dew",
    "pressure": "FILE:mtress/examples/weather.csv:pressure",
}


house_1.add(
    technologies.Photovoltaics(
        "pv0",
        (52.729, 8.181),
        nominal_power=10,
        weather=weather,
        surface_azimuth=180,
        surface_tilt=35,
        fixed=False,
    )
)

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "freq": "60T",
        "periods": 10,
        "tz": "Europe/Berlin",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="electricity_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="electricity_simple.png")


solved_model = solph_representation.solve(solve_kwargs={"tee": True})


solved_model.write("electricity.lp", io_options={"symbolic_solver_labels": True})
