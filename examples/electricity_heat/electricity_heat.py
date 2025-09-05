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
    demands.Electricity(
        name="electricity demand",
        time_series=[9, 13],
    )
)

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[0, 7, 12, 20, 30, 35, 55],
    )
)
house_1.add(
    demands.FixedTemperatureHeating(
        name="space_heating",
        min_flow_temperature=35,
        return_temperature=30,
        time_series=[50, 60],
    )
)

electric_heater = technologies.ResistiveHeater(
    name="ResistiveHeater",
    thermal_power_limit=None,
    maximum_temperature=100,
)
house_1.add(electric_heater)

house_1.add(
    technologies.HeatPump(
        name="HeatPump",
        method_cop="linear",
        options_cop = {
                35: (0.0850, 0.0526, 0.0613, 0.0018),  # A, E, F, G
                55: (0.0470, 0.0247, 0.0271, 0.0005),
                },
        thermal_power_limit=None,
        max_temp_primary=20,
        min_temp_primary=0,
        max_temp_secondary=35,
        min_temp_secondary=30,
    )
)

house_1.add(
    technologies.HeatSource(
        name="Air_HE",
        reservoir_temperature=12,
        maximum_working_temperature=40,
        minimum_working_temperature=0,
        nominal_power=1e4,
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

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = results(solved_model)
flows = get_flows(myresults)

solved_model.write(
    "electricity_heat.lp", io_options={"symbolic_solver_labels": True}
)

solph_representation.graph(flow_results=flows)


Qc= flows[('house_1','HeatPump','heat_budget_source'),('house_1','HeatPump','heat_budget')]
Pel = flows [('house_1','ElectricityCarrier','distribution'),('house_1','HeatPump','electricity')]

COP = Qc/Pel

print (COP)