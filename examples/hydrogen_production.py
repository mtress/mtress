"""Example to illustrate hydrogen production to meet hydrogen demand."""

from oemof.solph.processing import results
from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.Electricity(working_rate=35, demand_rate=0))

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
        nominal_power=1500,
        weather=weather,
        surface_azimuth=180,
        surface_tilt=35,
        fixed=True,
    )
)

house_1.add(
    demands.Electricity(
        name="electricity demand",
        time_series=[90, 30, 50, 34],
    )
)

house_1.add(
    carriers.Hydrogen(
        pressure_levels=[30, 70, 250],
    )
)

house_1.add(
    demands.Hydrogen(
        name="H2_demand",
        time_series=[3, 2, 5, 10],
        pressure=250,
    )
)

house_1.add(
    demands.HydrogenInjection(
        name="H2_Injection",
        pressure=30,
        ng_vol_flow=[15, 15, 10, 13],
        h2_vol_limit=10,
        revenue=5,
    )
)

house_1.add(
    demands.HydrogenPipeline(
        name="H2_Pipeline",
        pressure=70,
        h2_vol_flow=[55, 45, 45, 56],
        revenue=5,
    )
)

house_1.add(
    carriers.Heat(
        temperature_levels=[45],
        reference_temperature=10,
    )
)

house_1.add(
    demands.FixedTemperatureHeat(
        name="hot water",
        flow_temperature=45,
        return_temperature=10,
        time_series=[155, 125, 185, 213],
    )
)

house_1.add(technologies.PEMElectrolyzer(name="Ely", nominal_power=500))
house_1.add(technologies.HeatPump(name="hp0", thermal_power_limit=None))
house_1.add(technologies.H2Compressor(name="H2Compr", nominal_power=50))

house_1.add(
    technologies.AirHeatExchanger(name="ahe", air_temperatures=[3, 6, 13, 12])
)
solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 12:00:00",
        "end": "2021-07-10 15:00:00",
        "freq": "60T",
        "tz": "Europe/Berlin",
    },
)

solph_representation.build_solph_energy_system()
solph_representation.build_solph_model()

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

plot = solph_representation.graph(detail=True)
plot.render(outfile="hydrogen_heat_simple.png")

myresults = results(solved_model)
solved_model.write(
    "hydrogen_production.lp", io_options={"symbolic_solver_labels": True}
)
