"""Example to illustrate hydrogen production to meet hydrogen demand."""

import logging
import os
import pandas as pd
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
from mtress.technologies import PEM_ELECTROLYSER

LOGGER = logging.getLogger(__file__)

energy_system = MetaModel()

os.chdir(os.path.dirname(__file__))

house_1 = Location(name="house_1")

energy_system.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=70e-6))
house_1.add(
    carriers.GasCarrier(
        gases={
            HYDROGEN: [30],
        }
    )
)

house_1.add(
    demands.GasDemand(
        name="H2_demand",
        gas_type=HYDROGEN,
        time_series=[0.5, 2.5, 1.5],
        pressure=30,
    )
)

house_1.add(carriers.HeatCarrier(temperature_levels=[20, 40]))

house_1.add(
    technologies.OffsetElectrolyser(
        name="PEM_Ely",
        nominal_power=150e3,
        template=PEM_ELECTROLYSER,
    )
)

house_1.add(
    demands.FixedTemperatureHeating(
        name="heating_demand",
        min_flow_temperature=40,
        return_temperature=20,
        time_series=[3000, 3000, 3000],
    )
)

# add infinite source and sink for heat carrier
house_1.add(
    technologies.SlackNode(
        {carriers.HeatCarrier: 1e9},
    )
)

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-06-01 08:00:00",
        "end": "2022-06-01 11:00:00",
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
solph_representation.graph(
    flow_results=flows, units=units, flow_colours=flow_colours
)

solved_model.write("offset.lp", io_options={"symbolic_solver_labels": True})
