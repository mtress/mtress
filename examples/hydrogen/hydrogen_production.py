"""Example to illustrate hydrogen production to meet hydrogen demand."""

import os

from oemof.solph.processing import results

from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
from mtress.physics import HYDROGEN
from mtress.technologies import ALKALINE_ELECTROLYSER

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=0.35))

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
        nominal_power=15e5,
        weather=weather,
        surface_azimuth=180,
        surface_tilt=35,
        fixed=True,
    )
)

house_1.add(
    demands.Electricity(
        name="electricity demand",
        time_series=[9e4, 3e4, 5e4, 3.4e4],
    )
)

house_1.add(carriers.GasCarrier(gases={HYDROGEN: [30, 70, 250]}))

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
        working_rate=15,
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
    carriers.HeatCarrier(
        temperature_levels=[5, 10, 20, 30, 40, 55],
        reference_temperature=0,
    )
)

house_1.add(
    demands.FixedTemperatureHeating(
        name="hot water",
        min_flow_temperature=55,
        return_temperature=10,
        time_series=[155e3, 125e3, 185e3, 213e3],
    )
)

house_1.add(
    technologies.Electrolyser(
        name="Alk-Ely",
        nominal_power=5e5,
        template=ALKALINE_ELECTROLYSER,
    )
)

house_1.add(
    technologies.HeatPump(
        name="HP",
        thermal_power_limit=None,
        max_temp_primary=10,
        min_temp_primary=5,
        max_temp_secondary=55,
        min_temp_secondary=20,
    )
)
house_1.add(
    technologies.HeatSource(
        name="AHE",
        nominal_power=100e3,
        reservoir_temperature=[10, 20, 25, 30],
        minimum_working_temperature=10,
        maximum_working_temperature=30,
    )
)

house_1.add(
    technologies.GasCompressor(name="H2Compr", nominal_power=5e4, gas_type=HYDROGEN)
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

solved_model.write(
    "hydrogen_production.lp", io_options={"symbolic_solver_labels": True}
)
