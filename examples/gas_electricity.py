"""
Example to illustrate use of gas carrier and gas grid connection along with
CHP implementation for heat and power generation.
"""

from oemof.solph.processing import results
from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
import logging
LOGGER = logging.getLogger(__file__)
from mtress._helpers import get_flows
energy_system = MetaModel()

house_1 = Location(name="house_1")

energy_system.add_location(house_1)


house_1.add(carriers.Electricity())
house_1.add(technologies.ElectricityGridConnection(working_rate=35))
house_1.add(technologies.GasGridConnection(grid_pressure=20, working_rate=11))

weather = {
    "ghi": "FILE:mtress/examples/input_file.csv:ghi",
    "dhi": "FILE:mtress/examples/input_file.csv:dhi",
    "wind_speed": "FILE:mtress/examples/input_file.csv:wind_speed",
    "temp_air": "FILE:mtress/examples/input_file.csv:temp_air",
    "temp_dew": "FILE:mtress/examples/input_file.csv:temp_dew",
    "pressure": "FILE:mtress/examples/input_file.csv:pressure",
}

house_1.add(
    technologies.Photovoltaics(
        "pv0",
        (52.729, 8.181),
        nominal_power=800,
        weather=weather,
        surface_azimuth=180,
        surface_tilt=35,
        fixed=True,
    )
)

house_1.add(
    demands.Electricity(
        name="electricity_demand",
        time_series="FILE:mtress/examples/input_file.csv:electricity",
    )
)

house_1.add(
    carriers.Gas(pressure_levels=[20, 50], feed_in_pressure=20)
)

house_1.add(
    carriers.Heat(
        temperature_levels=[80, 20],
        reference_temperature=10,
    )
)


house_1.add(
    demands.HeatSink(
        name="Excess Heat",
        temperature_levels=80,
    )
)

house_1.add(technologies.CHP(name="CHP", thermal_temperature=80, nominal_power=100, pressure=50))
house_1.add(technologies.GasCompressor(name="NG_Compressor", nominal_power=50, gas_const=518.28,
                                       unit_conversion=11.2))

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-06-01 08:00:00",
        "end": "2022-06-06 18:00:00",
        "freq": "15T",
        "tz": "Europe/Berlin",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="hydrogen_plant_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="hydrogen_plant_simple.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

logging.info("Optimise the energy system")
myresults = results(solved_model)
flows = get_flows(myresults)

solved_model.write("hydrogen_plant.lp", io_options={"symbolic_solver_labels": True})
