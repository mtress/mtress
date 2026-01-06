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

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=350))

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[10, 15, 25, 45],
    )
)

house_1.add(
    demands.FixedTemperatureHeating(
        name="space_heating",
        min_flow_temperature=25,
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


Acoll = 1.95  # in m2
Rad_tot = 1000  # in W/m2 total radiation, beam and diffuse
Rad_nom = 1350  # in W/m2 total radiation, beam and diffuse

#######################
house_1.add(
    technologies.HeatSource(
        name="thColl",
        reservoir_temperature=[15, 15],
        maximum_working_temperature=45,
        minimum_working_temperature=10,
        conductivity_gain_factor=4.49 * Acoll / (Rad_nom * Acoll),
        non_thermal_gains=0.381 * Acoll * Rad_tot / (Rad_nom * Acoll),
        nominal_power=Rad_nom * Acoll,
        working_rate=0,
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

solved_model = solph_representation.solve(solve_kwargs={"tee": False})
myresults = Results(solved_model)
flows = myresults["flow"]
units = get_flow_units(solph_representation)
flow_colours = get_energy_types(solph_representation)
solph_representation.graph(
    flow_results=flows, units=units, flow_colours=flow_colours
)

label1 = ("source_reservoir", "thColl", "house_1")
label2 = ("heat_source", "thColl", "house_1")
Qcoll = flows[str(label1), str(label2)]

label1 = ("heat_source", "thColl", "house_1")
label2 = ("source_15", "thColl", "house_1")
Qcoll_30 = flows[str(label1), str(label2)]

label2 = ("source_45", "thColl", "house_1")
Qcoll_45 = flows[str(label1), str(label2)]

label2 = ("source_25", "thColl", "house_1")
Qcoll_25 = flows[str(label1), str(label2)]

print("Qcoll:", Qcoll.sum() / 2)
print("Qcoll_15:", Qcoll_30.sum() / 2)
print("Qcoll_25:", Qcoll_25.sum() / 2)
print("Qcoll_45:", Qcoll_45.sum() / 2)
