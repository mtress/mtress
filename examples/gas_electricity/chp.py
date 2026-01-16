"""
CHP implementation for heat and power generation.
"""

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
from mtress.physics import NATURAL_GAS
from mtress.technologies import NATURALGAS_CHP


LOGGER = logging.getLogger(__file__)

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")

energy_system.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=50e-6))
house_1.add(
    carriers.GasCarrier(
        gases={
            NATURAL_GAS: [10],
        }
    )
)

house_1.add(carriers.HeatCarrier(temperature_levels=[20, 80]))
house_1.add(
    technologies.CHP(
        name="Gas_CHP",
        gas_type={NATURAL_GAS: 1},
        nominal_power=1e5,
        template=NATURALGAS_CHP,
        input_pressure=1,
    )
)
house_1.add(
    technologies.GasGridConnection(
        gas_type=NATURAL_GAS,
        grid_pressure=10,
        working_rate=5,
    )
)

# Add heat demands
house_1.add(
    demands.FixedTemperatureHeating(
        name="heat_demand",
        min_flow_temperature=80,
        return_temperature=20,
        time_series=[1000],
    )
)
house_1.add(
    demands.Electricity(
        name="electricity_demand",
        time_series=[1000],
    )
)
solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-06-01 08:00:00",
        "end": "2022-06-01 09:00:00",
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
    flow_results=flows,
    units=units,
    flow_colours=flow_colours,
)

solved_model.write("chp.lp", io_options={"symbolic_solver_labels": True})
