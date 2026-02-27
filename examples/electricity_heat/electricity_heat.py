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
house_1.add(technologies.ElectricityGridConnection(working_rate=0.035))

house_1.add(
    demands.Electricity(
        name="electricity demand",
        time_series=[9, 13],
    )
)

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[-5, 0, 7, 12, 20, 30, 50, 55],
    )
)
house_1.add(
    demands.FixedTemperatureHeating(
        name="space_heating",
        min_flow_temperature=55,
        return_temperature=50,
        time_series=[50, 60],
    )
)

electric_heater = technologies.ResistiveHeater(
    name="ResistiveHeater",
    thermal_power_limit=None,
    maximum_temperature=100,
)
house_1.add(electric_heater)

cop_ref_point = technologies.COPReference(
    cop=2.9,
    warm_side_in=30,
    warm_side_out=35,
    cold_side_in=0,
    cold_side_out=-5,
)


house_1.add(
    technologies.HeatPump(
        name="HeatPump",
        method_cop="linear",
        ref_cop=cop_ref_point,
        # defining your fitted coefficients for 35 and 55 supply temperatures - caution: using other temperature levels than 35 and 55 will give error.
        options_cop={
            "cop_eqs": {
                35: (0.100, 0.0409, 0.0477, 0.0014),  # A, E, F, G
                55: (0.0644, 0.0208, 0.0229, 0.0004),  # A, E, F, G
            }
        },
        thermal_power_limit=None,
        max_temp_primary=20,
        min_temp_primary=-20,
        max_temp_secondary=55,
        min_temp_secondary=50,
    )
)

house_1.add(
    technologies.HeatSource(
        name="Air_HE",
        reservoir_temperature=0,
        maximum_working_temperature=40,
        minimum_working_temperature=-20,
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
myresults = Results(solved_model)
flows = myresults["flow"]
units = get_flow_units(solph_representation)
flow_colours = get_energy_types(solph_representation)
solph_representation.graph(
    flow_results=flows, units=units, flow_colours=flow_colours
)

solved_model.write(
    "electricity_heat.lp", io_options={"symbolic_solver_labels": True}
)

solph_representation.graph(flow_results=flows)


Qc = flows[
    ("heat_budget_source", "HeatPump", "house_1"),
    ("heat_budget", "HeatPump", "house_1"),
]
Pel = flows[
    ("distribution", "ElectricityCarrier", "house_1"),
    ("electricity", "HeatPump", "house_1"),
]

COP = Qc / Pel
house_1
print(COP)
