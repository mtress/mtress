"""Simple example to illustrate heat production from resistive heater"""

import os

from oemof.solph.processing import results

from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
from mtress._helpers import get_flows
from mtress.physics import HYDROGEN
from mtress.technologies import PEM_ELECTROLYSER

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.Electricity())
house_1.add(technologies.ElectricityGridConnection(working_rate=35))

house_1.add(
    technologies.Electrolyser(
        name="ELY",
        nominal_power=100000,
        minimum_temperature=20,
        template=PEM_ELECTROLYSER,
    )
)

house_1.add(
    demands.HeatSink(
        name="Excess Heat",
        temperature_levels=50,
    )
)

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[20, 50],
        reference_temperature=10,
    )
)
house_1.add(carriers.GasCarrier(gases={HYDROGEN: [30]}))
house_1.add(
    demands.GasDemand(
        name="H2_Dem", gas_type=HYDROGEN, pressure=30, time_series=[0.5, 0.5]
    )
)


solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 02:00:00",
        "freq": "60T",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="electrolyser_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="electrolyser_simple.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = results(solved_model)
flows = get_flows(myresults)

solved_model.write("electrolyser.lp", io_options={"symbolic_solver_labels": True})
