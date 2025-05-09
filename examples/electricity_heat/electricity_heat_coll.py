"""
Basic working 'electricity and heat' example.

Basic working 'electricity and heat' example which includes a location (house),
electricity wise: an electricity carrier which acts as a electricity
source/supply from the official grid (working price of 0.035 ct/Wh) as well as
a demand (consumer) with a demand time series.
And heat wise: a heat carrier, a heat pump, an heat exchanger as well as
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
        temperature_levels=[ 10, 15,20, 25, 30, 40],
    )
)

house_1.add(
    demands.FixedTemperatureHeating(
        name="space_heating",
        min_flow_temperature=20,
        return_temperature=15,
        time_series=[2000e3, 2000e3],
    )
)

electric_heater = technologies.ResistiveHeater(
    name="ResistiveHeater",
    thermal_power_limit=None,
    maximum_temperature=100,
)
house_1.add(electric_heater)
"""
house_1.add(
    technologies.HeatPump(
        name="HeatPump",
        thermal_power_limit=None,
        max_temp_primary=25,
        min_temp_primary=-10,
        max_temp_secondary=55,
        min_temp_secondary=30,
    )
) """

#Yearly_rad = 1765e3 # data from Solarkeymark in Wh/m2a
# Npro_output = 557e3 # data from npro in Wh/m2a
Power_O_keymark = 115 #in W, 115 W for 10K temp diff; 767 W for 0K; Gb= 850, Gd= 150 and 2m2 coll area
Acoll= 2 #in m2
Rad_beam = 850 # in W/m2 total radiation, beam and diffuse
Rad_diff = 150 # in W/m2 total radiation, beam and diffuse
K_d = 0.827
Rad_nom = 1350 # in W/m2 total radiation, beam and diffuse

house_1.add(# parameters for the WISC coll (for npro validation) - nu0=0,329; a1=40,94, global radiation at 25° in Athens = 1985,48 kWh/m2a; Result (npro) =557,93 kWh/m2
    technologies.HeatSource(
        name="thColl",
        reservoir_temperature=[15, 15],
        maximum_working_temperature=20,
        minimum_working_temperature=10,
        conductivity=40.94*Acoll,
        non_thermal_gains=0.329*Rad_beam*Acoll+Acoll*K_d*Rad_diff*0.329, # this factor is the nu_0 times the radiation (as time series in Wh/h) for the total collector area
        nominal_power=Rad_nom*Acoll, # this factor needs to be the maximum radiation on the collector plane for a given timestep (e.g. for hours in Wh/h) for the total collector area
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

Qcoll = flows[('house_1', 'thColl', 'source_reservoir'), ('house_1', 'thColl', 'heat_source')]
#Qcoll_10 = flows [('house_1', 'thColl', 'heat_source'), ('house_1', 'thColl', 'source_10')].sum
#Qcoll_15 = flows [('house_1', 'thColl', 'heat_source'), ('house_1', 'thColl', 'source_15')].sum
#Qcoll_25 = flows [('house_1', 'thColl', 'heat_source'), ('house_1', 'thColl', 'source_25')]
Overestimation = Qcoll - Power_O_keymark #Npro_output


print(Qcoll)
print( Overestimation)
