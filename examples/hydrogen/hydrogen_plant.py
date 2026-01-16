"""Example to illustrate hydrogen production to meet hydrogen demand."""

import logging
import os
from oemof.solph import Results
from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress._helpers import get_flow_units, get_energy_types
from mtress.physics import HYDROGEN
from mtress.technologies import AFC, PEM_ELECTROLYSER

LOGGER = logging.getLogger(__file__)

energy_system = MetaModel()

os.chdir(os.path.dirname(__file__))

house_1 = Location(name="house_1")

energy_system.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(
    technologies.ElectricityGridConnection(working_rate=70e-3, revenue=0)
)
house_1.add(
    carriers.GasCarrier(
        gases={
            HYDROGEN: [5, 30, 40, 70],
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
    technologies.RenewableElectricitySource(
        "pv0",
        nominal_power=2e6,
        specific_generation="FILE:../input_file.csv:pv",
        fixed=False,
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
        pressure=40,
    )
)
house_1.add(
    technologies.H2Storage(
        name="H2_Storage",
        volume=5,
        power_limit=10,
    )
)
house_1.add(carriers.HeatCarrier(temperature_levels=[20, 40]))
house_1.add(
    technologies.Electrolyser(
        name="PEM_Ely",
        nominal_power=1500e3,
        template=PEM_ELECTROLYSER,
    )
)
house_1.add(
    technologies.FuelCell(
        name="AFC", nominal_power=10e3, gas_input_pressure=5, template=AFC
    )
)

house_1.add(
    technologies.HeatSink(
        name="Heat_Sink",
        reservoir_temperature=20,
        minimum_working_temperature=20,
        maximum_working_temperature=40,
        nominal_power=200e5,
    )
)
house_1.add(
    technologies.GasCompressor(
        name="H2Compr", nominal_power=50e3, gas_type=HYDROGEN
    )
)

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-07-01 08:00:00",
        "end": "2022-07-01 09:00:00",
        "freq": "15min",
        "tz": "Europe/Berlin",
    },
)

solph_representation.build_solph_model()
solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = Results(solved_model)
flows = myresults["flow"]
units = get_flow_units(solph_representation)
flow_colours = get_energy_types(solph_representation)
solph_representation.graph(
    flow_results=flows,
    units=units,
    flow_colours=flow_colours,
)

solved_model.write(
    "hydrogen_plant.lp", io_options={"symbolic_solver_labels": True}
)
