"""Example to illustrate hydrogen production to meet hydrogen demand."""

from oemof.solph.processing import results
from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
import logging
LOGGER = logging.getLogger(__file__)
from mtress._helpers import get_flows
energy_system = MetaModel()
from mtress.technologies._mixed_storage import Implementation

house_1 = Location(name="house_1")

energy_system.add_location(house_1)


house_1.add(carriers.Electricity(working_rate=1, demand_rate=0))

weather = {
    "ghi": "FILE:mtress/examples/elec_heat_h2_weather.csv:ghi",
    "dhi": "FILE:mtress/examples/elec_heat_h2_weather.csv:dhi",
    "wind_speed": "FILE:mtress/examples/elec_heat_h2_weather.csv:wind_speed",
    "temp_air": "FILE:mtress/examples/elec_heat_h2_weather.csv:temp_air",
    "temp_dew": "FILE:mtress/examples/elec_heat_h2_weather.csv:temp_dew",
    "pressure": "FILE:mtress/examples/elec_heat_h2_weather.csv:pressure",
}

house_1.add(
    technologies.Photovoltaics(
        "pv0",
        (52.729, 8.181),
        nominal_power=2000,
        weather=weather,
        surface_azimuth=180,
        surface_tilt=35,
        fixed=True,
    )
)

house_1.add(
    demands.Electricity(
        name="electricity_demand",
        time_series="FILE:mtress/examples/elec_heat_h2_weather.csv:electricity",
    )
)

house_1.add(
    carriers.Hydrogen(
        pressure_levels=[1, 30, 350],
    )
)

house_1.add(
    demands.Hydrogen(
        name="H2_demand",
        time_series="FILE:mtress/examples/elec_heat_h2_weather.csv:h2_demand",
        pressure=350,
    )
)


house_1.add(
    technologies.H2Storage(
        name="H2_Storage",
        volume=0.59,
        power_limit=10,
        multiplexer_implementation= Implementation.FLEXIBLE
    )
)

house_1.add(
    carriers.Heat(
        temperature_levels=[60],
        reference_temperature=20,
    )
)


house_1.add(
    demands.HeatSink(
        name="Excess Heat",
        temperature_levels=60,
    )
)

house_1.add(technologies.PEMElectrolyzer(name="Ely", nominal_power=220))
house_1.add(technologies.PEMFuelCell(name="Fuel_Cell", nominal_power=100))
house_1.add(technologies.H2Compressor(name="H2Compr", nominal_power=100))

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-06-01 08:00:00",
        "end": "2022-06-03 18:00:00",
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
