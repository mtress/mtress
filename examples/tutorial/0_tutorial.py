# %%[imports]
import os
import warnings

import matplotlib.pyplot as plt
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
from mtress._helpers import get_energy_types, get_flow_units

# ignore warnings
warnings.filterwarnings("ignore")

# set dir
os.chdir(os.path.dirname(__file__))


# %%[input_data]
# load input data from file
print(
    "Data is licensed from M. Schlemminger, T. Ohrdes, E. Schneider,"
    " and M. Knoop. Under Creative Commons Attribution 4.0 International"
    " License. It is also available at doi: 10.5281/zenodo.5642902."
    " (We use building 27 plus the south-facing PV"
    " from that dataset.)"
)
print(
    "Data is has been aggregated to hourly data. "
    "The year has been altered from 2019 to 2025."
)
data = pd.read_csv("data.csv", index_col="time")

# lets look at some spring days
data: pd.DataFrame = data[
    "2025-04-01 00:00:00+01:00":"2025-04-10 23:00:00+01:00"
]

# extract data for simple usage
elec_demand = data["electricity demand (W)"]
heat_demand = data["heat demand (W)"]

# plot data
data.plot()
plt.xticks(rotation=15)
plt.title("demand and pv data")
plt.show()


# %%[base_model_factory]
def base_model_factory() -> tuple[MetaModel, Location]:
    # create meta model
    energy_system = MetaModel()

    # create location and add it to meta model
    loc = Location(name="loc")
    energy_system.add(loc)

    # create carriers for the energy types in our system
    loc.add(carriers.ElectricityCarrier())

    # add electricity grid connection
    # 32 ct per kW import and 6 ct per kW export
    loc.add(
        technologies.ElectricityGridConnection(
            working_rate=0.00032, revenue=0.00006
        )
    )

    # add electricity demand from loaded time series
    loc.add(demands.Electricity(name="e_demand", time_series=elec_demand))

    # add a pv system and provide pv time series
    loc.add(
        technologies.RenewableElectricitySource(
            name="pv",
            nominal_power=6,  # installed capacity
            specific_generation=data["PV (W/Wp)"],
        )
    )

    return energy_system, loc


# %%[optimization_setup]
def get_results(model: MetaModel) -> tuple[SolphModel, Results]:
    solph_representation = SolphModel(
        model,
        timeindex={
            "start": "2025-04-01 00:00:00",
            "freq": "60min",  # hourly
            "periods": 241,  # num of steps in time_series + 1
            "tz": "Europe/Berlin",
        },
    )
    solph_representation.build_solph_model()

    # solve
    solved_model = solph_representation.solve()  # solve_kwargs={"tee": True}

    # get results
    results = Results(solved_model)

    return (solph_representation, results)


# %%[build_model]
energy_system, loc = base_model_factory()

# %%[solve]
solph_representation, results = get_results(energy_system)

# get all flows
flows = results["flow"]

# %%[plot_model]
# for plotting of the system, get units and energy types
units = get_flow_units(solph_representation)
flow_colours = get_energy_types(solph_representation)

solph_representation.graph(
    flow_results=flows,
    units=units,
    flow_colours=flow_colours,
    path="0_model.png",
)

# %%[inspect_resuts]
# get optimal objective value
print("= loc 1 ========================================")
print(
    "optimal objective value:",
    results._solver_results["Problem"][0]["Lower bound"],
    "€",
)

# get flows for electricity import and export
grid_import = flows[
    str(("source_import", "ElectricityGridConnection", "loc")),
    str(("grid_import", "ElectricityGridConnection", "loc")),
]
grid_export = flows[
    str(("grid_export", "ElectricityGridConnection", "loc")),
    str(("sink_export", "ElectricityGridConnection", "loc")),
]

# sanity check results
print("total import:", sum(grid_import), "Wh")
print("total export:", sum(grid_export), "Wh")
print("================================================")

# plot electricity import and export
plt.close()  # fresh figure
plt.plot(grid_import, label="import", color="red")
plt.plot(grid_export, label="export", color="green")
plt.legend()
plt.title("electricity im-/export | loc 1")
plt.xticks(rotation=15)
plt.show()

# %%[extend_model_heat_demand]
# new meta model and location
energy_system, loc = base_model_factory()

# add a heat carrier with levels 20 and 30
loc.add(carriers.HeatCarrier(temperature_levels=[20, 30]))
# add heating demand
loc.add(
    demands.FixedTemperatureHeating(
        "h_demand",
        min_flow_temperature=30,
        return_temperature=20,
        time_series=heat_demand,
    )
)
# for now, add slack to fullfil heating demand
loc.add(technologies.SlackNode({carriers.HeatCarrier: 1e9}))

# %%[REPEAT:solve]
solph_representation, results = get_results(energy_system)

# get all flows
flows = results["flow"]

# %%[REPEAT:plot_model]
# for plotting of the system, get units and energy types
units = get_flow_units(solph_representation)
flow_colours = get_energy_types(solph_representation)
solph_representation.graph(
    flow_results=flows,
    units=units,
    flow_colours=flow_colours,
    path="0_model_with_heat.png",
)

# %%[REPEAT:inspect_resuts]
# get optimal objective value
print("= loc 2 ========================================")
print(
    "optimal objective value:",
    results._solver_results["Problem"][0]["Lower bound"],
    "€",
)
print("================================================")

# system is way to expensive with slack node
# --> we need a heating technology!

# %%[extend_model_electric_heater]
# new meta model and location
energy_system, loc = base_model_factory()

# add a heat carrier with levels 20 and 30
loc.add(carriers.HeatCarrier(temperature_levels=[20, 30]))
# add heating demand
loc.add(
    demands.FixedTemperatureHeating(
        "h_demand",
        min_flow_temperature=30,
        return_temperature=20,
        time_series=heat_demand,
    )
)
# add simple resistive heater
loc.add(
    technologies.ResistiveHeater(
        name="heater",
        maximum_temperature=30,
        minimum_temperature=20,
    )
)

# %%[REPEAT:solve]
solph_representation, results = get_results(energy_system)

# get all flows
flows = results["flow"]

# %%[REPEAT:plot_model]
# for plotting of the system, get units and energy types
units = get_flow_units(solph_representation)
flow_colours = get_energy_types(solph_representation)

solph_representation.graph(
    flow_results=flows,
    units=units,
    flow_colours=flow_colours,
    path="0_model_with_heater.png",
)

# %%[REPEAT:inspect_resuts]
# get optimal objective value
print("= loc 3 ========================================")
print(
    "optimal objective value:",
    results._solver_results["Problem"][0]["Lower bound"],
    "€",
)
print("================================================")

# get flows for electricity import and export
grid_import = flows[
    str(("source_import", "ElectricityGridConnection", "loc")),
    str(("grid_import", "ElectricityGridConnection", "loc")),
]
grid_export = flows[
    str(("grid_export", "ElectricityGridConnection", "loc")),
    str(("sink_export", "ElectricityGridConnection", "loc")),
]
# plot electricity import and export
plt.close()  # fresh figure
plt.plot(grid_import, label="import", color="red")
plt.plot(grid_export, label="export", color="green")
plt.legend()
plt.title("electricity im-/export | loc 1")
plt.xticks(rotation=15)
plt.show()

# %%[extend_model_heat_storage]
# new meta model and location
energy_system, loc = base_model_factory()

# add a heat carrier with levels 20 and 30
loc.add(carriers.HeatCarrier([20, 30]))
# add heating demand
loc.add(
    demands.FixedTemperatureHeating(
        "h_demand",
        min_flow_temperature=30,
        return_temperature=20,
        time_series=heat_demand,
    )
)
# add simple resistive heater
loc.add(
    technologies.ResistiveHeater(
        name="heater",
        maximum_temperature=30,
        # minimum_temperature=20,
    )
)
# add heat storage
loc.add(
    technologies.LayeredHeatStorage(
        name="heat_storage",
        diameter=0.5,
        volume=2,
        power_limit=7500,
        ambient_temperature=10,
        min_temperature=10,
        max_temperature=50,
        u_value=0.1,
    )
)


# %%[REPEAT:solve]
solph_representation, results = get_results(energy_system)

# get all flows
flows = results["flow"]

# get storage content and losses
storage_content = results["storage_content"]
storage_losses = results["storage_losses"]

storage_content[storage_content < 0] = 0

# %%[REPEAT:plot_system]
# for plotting of the system, get units and energy types
units = get_flow_units(solph_representation)
flow_colours = get_energy_types(solph_representation)

solph_representation.graph(
    flow_results=flows,
    units=units,
    flow_colours=flow_colours,
    path="0_model_with_heater_and_storage.png",
)

# %%[REPEAT:inspect_resuts]
# get optimal objective value
print("= loc 4 ========================================")
print(
    "optimal objective value:",
    results._solver_results["Problem"][0]["Lower bound"],
    "€",
)
print("================================================")

# get flows for electricity import and export
grid_import = flows[
    str(("source_import", "ElectricityGridConnection", "loc")),
    str(("grid_import", "ElectricityGridConnection", "loc")),
]
grid_export = flows[
    str(("grid_export", "ElectricityGridConnection", "loc")),
    str(("sink_export", "ElectricityGridConnection", "loc")),
]

# plot electricity import and export
plt.close()  # fresh figure
plt.plot(grid_import, label="import", color="red")
plt.plot(grid_export, label="export", color="green")
plt.legend()
plt.title("electricity im-/export | loc 4")
plt.xticks(rotation=15)
plt.show()

# plot heat storage content
plt.close()  # fresh figure
storage_content.plot.area()
plt.title("heat storage content")
plt.show()


# %%[interactive_results]
# solph_representation.graph_interactive(
#     flow_results=flows,
#     units=units,
#     flow_colours=flow_colours,
# )
