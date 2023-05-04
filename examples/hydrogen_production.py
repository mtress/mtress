"""Example to illustrate hydrogen production via Electrolyser and compression to meet
   hydrogen demand"""

from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
from mtress._helpers._visualization import generate_graph
from oemof.solph.processing import results

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add_carrier(carriers.Electricity(working_rate=35, demand_rate=0))

house_1.add_demand(demands.Hydrogen(name="H2_demand", time_series=[4, 5, 5, 10], pressure=100))

house_1.add_demand(
    demands.Electricity(
        name="electricity demand",
        time_series=[32, 12, 12, 34],
    )
)

house_1.add_carrier(
    carriers.Hydrogen(
        pressure_levels=[30, 100],
    ))

house_1.add_carrier(
    carriers.Heat(
        temperature_levels=[45],
        reference_temperature=10,
    ))

house_1.add_demand(
    demands.FixedTemperatureHeat(
        name="hot water",
        flow_temperature=45,
        return_temperature=10,
        time_series=[55, 75, 85, 13],
    )
)

house_1.add_technology(technologies.PEMElectrolyzer(name="Ely",nominal_power=500))
house_1.add_technology(technologies.HeatPump(name="hp0", thermal_power_limit=None))
house_1.add_technology(technologies.H2Compressor(name='H2Compr', nominal_power=5))

house_1.add_technology(
    technologies.AirHeatExchanger(name="ahe", air_temperatures=[3, 6, 13, 12])
)
solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 03:00:00",
        "freq": "60T",
    },
)

solph_representation.build_solph_energy_system()
solph_representation.build_solph_model()

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

plot = solph_representation.graph(detail=False)
plot.render(outfile="hydrogen_heat_simple.png")

myresults= results(solved_model)
solved_model.write("hydrogen_production.lp", io_options={"symbolic_solver_labels": True})
