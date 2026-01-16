"""Example to illustrate hydrogen production to meet hydrogen demand."""

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
from mtress.technologies import ALKALINE_ELECTROLYSER

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=0.35))
house_1.add(
    technologies.RenewableElectricitySource(
        "pv0",
        nominal_power=15e5,
        specific_generation="FILE:../input_file.csv:pv",
        fixed=False,
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

house_1.add(carriers.HeatCarrier(temperature_levels=[5, 10, 20, 30, 40, 55]))

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
    technologies.GasCompressor(
        name="H2Compr", nominal_power=5e4, gas_type=HYDROGEN
    )
)

house_1.add(technologies.SlackNode())

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-07-10 12:00:00",
        "end": "2022-07-10 16:00:00",
        "freq": "60min",
        "tz": "Europe/Berlin",
    },
)

solph_representation.build_solph_model()

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = Results(solved_model)
flows = myresults["flow"]
units = get_flow_units(solph_representation)
flow_colours = get_energy_types(solph_representation)
# solph_representation.graph_interactive(
#     flow_results=flows, units=units, flow_colours=flow_colours
# )
