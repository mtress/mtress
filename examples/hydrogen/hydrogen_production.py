"""Example to illustrate hydrogen production to meet hydrogen demand."""
import os

from oemof.solph.processing import results
from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
from mtress.carriers import HYDROGEN

os.chdir(os.path.dirname (__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.Electricity())
house_1.add(technologies.ElectricityGridConnection(working_rate=35))

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
    carriers.GasCarrier(
        gases={HYDROGEN: [30, 70, 250]}
    )
)

house_1.add(
    demands.GasDemand(
        name="H2_demand",
        gas_type=HYDROGEN,
        time_series=[3, 2, 5, 10],
        pressure=250,
    )
)

house_1.add(
    technologies.GasGridConnection(
        name="low_pressure",
        gas_type=HYDROGEN,
        grid_pressure=30,
    )
)

house_1.add(
    technologies.GasGridConnection(
        name="high_pressure",
        gas_type=HYDROGEN,
        grid_pressure=70,
        revenue=7,
        working_rate=15,
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
house_1.add(technologies.GasCompressor(name="H2Compr", nominal_power=50, gas_type=HYDROGEN))

house_1.add(
    technologies.AirHeatExchanger(name="ahe", air_temperatures=[3, 6, 13, 12])
)
solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 12:00:00",
        "end": "2021-07-10 16:00:00",
        "freq": "60T",
        "tz": "Europe/Berlin",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="hydrogen_production_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="hydrogen_production_simple.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

myresults = results(solved_model)

solved_model.write("hydrogen_production.lp", io_options={"symbolic_solver_labels": True})
