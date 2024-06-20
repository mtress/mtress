import os

from oemof.solph.processing import results

from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
from mtress._helpers import get_flows

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[20, 30],
        reference_temperature=10,
    )
)
house_1.add(
    demands.FixedTemperatureHeating(
        name="space heating",
        min_flow_temperature=30,
        return_temperature=20,
        time_series=[50, 50],
    )
)

house_1.add(
    technologies.AirHeatExchanger(
        name="ahe", air_temperatures=45, minimum_temperature=20
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
plot.render(outfile="air_heat_exchanger_source.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = results(solved_model)
flows = get_flows(myresults)
