"""Example to illustrate hydrogen production via Electrolyser and compression to meet hydrogen demand of the Refueling Station"""

from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
from mtress._helpers._visualization import generate_graph


energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add_carrier(carriers.Electricity(working_rate=35, demand_rate=0))

house_1.add_demand(demands.Hydrogen(name="H2_demand",time_series=[2], pressure= 250))


house_1.add_carrier(
    carriers.Hydrogen(
        pressure_levels=[30, 250],
    ))
"""house_1.add_carrier(
    carriers.Heat(
        temperature_levels=[20, 30, 55],
        reference_temperature=10,
    ))"""


house_1.add_technology(technologies.PEMElectrolyzer(name="Electrolyser",nominal_power=5))

house_1.add_technology(technologies.H2Compressor(name='H2Compressor',nominal_power= 0.5))

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 00:00:00",
        "freq": "60T",
    },
)

solph_representation.build_solph_energy_system()
solph_representation.build_solph_model()

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

plot = generate_graph(solved_model.es)
plot.render(format="png", renderer="cairo", formatter="gdiplus")

solved_model.write("hydrogen_production.lp", io_options={"symbolic_solver_labels": True})