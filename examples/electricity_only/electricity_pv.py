"""
Basic working 'electricity' example.
"""

import os

from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=35))

house_1.add(demands.Electricity(name="demand0", time_series=10))

weather = {
    "ghi": "FILE:../weather.csv:ghi",
    "dhi": "FILE:../weather.csv:dhi",
    "wind_speed": "FILE:../weather.csv:wind_speed",
    "temp_air": "FILE:../weather.csv:temp_air",
    "temp_dew": "FILE:../weather.csv:temp_dew",
    "pressure": "FILE:../weather.csv:pressure",
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
plot.render(outfile="electricity_pv_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="electricity_pv_simple.png")


solved_model = solph_representation.solve(solve_kwargs={"tee": True})


solved_model.write("electricity_pv.lp", io_options={"symbolic_solver_labels": True})
