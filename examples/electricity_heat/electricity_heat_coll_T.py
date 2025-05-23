"""
Basic working 'electricity_heat_coll' example.

Basic working example which includes a location (house),
electricity wise: an electricity carrier which acts as a electricity
source/supply from the official grid (working price of 0.035 ct/Wh) which
is solely used to supply the required electricity for an electric
heater used as back up to the collector.
And heat wise: a heat carrier, a solar collector as well as
a heat demand time series.

At first an energy system (here meta_model) is defined with a time series
(index). Afterwards a location is defined and added to the energysystem. Then
the electricity carrier and electricity demand (time series) are added to the
energysystem. Furthermore a heat carrier is defined with specific temp-
erature level(s) and a reference temperature. Then  a heat demand (time series)
is added with a certain flow and return temperature. Lastly, a heat pump with
a possible thermal power limit and heat exchanger with a certain air
temperature are added to the energy system.

Finally, the energy system is optimised/solved via meta_model.solve, a plot is
created and the solver output is written to an .lp file.
"""

import os
import pandas as pd

from oemof.solph.processing import results

from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress._helpers import get_flows

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=0.035))

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[10, 15, 25, 30, 45],
    )
)

house_1.add(
    demands.FixedTemperatureHeating(
        name="space_heating",
        min_flow_temperature=45,
        return_temperature=10,
        time_series=[2e3, 2e3],
    )
)

electric_heater = technologies.ResistiveHeater(
    name="ResistiveHeater",
    thermal_power_limit=None,
    maximum_temperature=100,
)
house_1.add(electric_heater)


Acoll = 2  # in m2
# Rad_beam = 850 # in W/m2 beam
# Rad_diff = 150 # in W/m2  diffuse
# K_d = 0.97
Rad_tot = 1000  # in W/m2 total radiation, beam and diffuse
Rad_nom = 1350  # in W/m2 total radiation, beam and diffuse


#######################
house_1.add(
    technologies.HeatSource(
        name="thColl",
        reservoir_temperature=[15, 15],
        maximum_working_temperature=45,
        minimum_working_temperature=15,
        conductivity_gain_factor=32.56 * Acoll,
        non_thermal_gains=0.381
        * Acoll
        * Rad_tot,
        nominal_power=Rad_nom
        * Acoll,
    )
)

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 02:00:00",
        "freq": "60min",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="electricity_heat_coll_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="electricity_heat_coll_simple.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": False})
myresults = results(solved_model)
flows = get_flows(myresults)

plot = solph_representation.graph(detail=True, flow_results=flows)
plot.render(outfile="electricity_heat_coll_results.png")

Qcoll = flows[
    ("house_1", "thColl", "source_reservoir"),
    ("house_1", "thColl", "heat_source"),
]
Qcoll_30 = flows[
    ("house_1", "thColl", "heat_source"), ("house_1", "thColl", "source_30")
]
Qcoll_45 = flows[
    ("house_1", "thColl", "heat_source"), ("house_1", "thColl", "source_45")
]
Qcoll_25 = flows[
    ("house_1", "thColl", "heat_source"), ("house_1", "thColl", "source_25")
]

print(Qcoll)
