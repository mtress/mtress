"""Example to illustrate hydrogen production to meet hydrogen demand."""

import logging
import os

from oemof.solph.processing import results

from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
from mtress.physics import HYDROGEN
from mtress.technologies import AFC, PEM_ELECTROLYSER

LOGGER = logging.getLogger(__file__)
from mtress._helpers import get_flows

energy_system = MetaModel()

os.chdir(os.path.dirname(__file__))

house_1 = Location(name="house_1")

energy_system.add_location(house_1)


house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=0.70))

house_1.add(
    carriers.GasCarrier(
        gases={
            HYDROGEN: [20, 30, 60, 350],
        }
    )
)
weather = {
    "ghi": "FILE:../input_file.csv:ghi",
    "dhi": "FILE:../input_file.csv:dhi",
    "wind_speed": "FILE:../input_file.csv:wind_speed",
    "temp_air": "FILE:../input_file.csv:temp_air",
    "temp_dew": "FILE:../input_file.csv:temp_dew",
    "pressure": "FILE:../input_file.csv:pressure",
}

house_1.add(
    technologies.Photovoltaics(
        "pv0",
        (52.729, 8.181),
        nominal_power=8e6,
        weather=weather,
        surface_azimuth=180,
        surface_tilt=35,
        fixed=True,
    )
)

house_1.add(
    demands.Electricity(
        name="electricity_demand",
        time_series="FILE:../input_file.csv:electricity",
    )
)

house_1.add(
    demands.GasDemand(
        name="H2_demand",
        gas_type=HYDROGEN,
        time_series="FILE:../input_file.csv:h2_demand",
        pressure=60,
    )
)


house_1.add(
    technologies.H2Storage(
        name="H2_Storage",
        volume=15,
        power_limit=10,
    )
)

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[20, 40],
        reference_temperature=10,
    )
)

house_1.add(
    demands.FixedTemperatureHeating(
        name="hot water",
        min_flow_temperature=40,
        return_temperature=20,
        time_series="FILE:../input_file.csv:heat",
    )
)

house_1.add(
    technologies.Electrolyser(
        name="PEM_Ely", nominal_power=10e5, template=PEM_ELECTROLYSER
    )
)
house_1.add(
    technologies.FuelCell(
        name="AFC", nominal_power=5e5, gas_input_pressure=20, template=AFC
    )
)
house_1.add(
    technologies.GasCompressor(name="H2Compr", nominal_power=1e5, gas_type=HYDROGEN)
)

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-06-01 08:00:00",
        "end": "2022-06-01 18:00:00",
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
