from oemof.solph import Results

from mtress import Location, MetaModel, SolphModel, carriers, demands
from mtress.physics import HYDROGEN


def test_basic_initialisation():

    energy_system = MetaModel()

    loc = Location("house")

    energy_system.add_location(loc)

    gc = carriers.GasCarrier(location=loc)

    gd = demands.GasDemand(
        "hydrogen_demand",
        gas_type=HYDROGEN,
        pressure=2,
        time_series=[0, 0, 0],
        location=loc,
    )

    assert gd.label == ("hydrogen_demand", "house")
    assert gd.parent == loc
    assert gd._time_series == [0, 0, 0]

    assert len(gd.inbound_interfaces) == 1
    assert len(gd.outbound_interfaces) == 0

    solph_representation = SolphModel(
        energy_system,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 03:00:00",
            "freq": "60min",
        },
    )

    solph_representation.graph(
        path="tests/integration_tests/demands/test_gas_demand.png"
    )

    solved_model = solph_representation.solve(solve_kwargs={"tee": False})

    myresults = Results(solved_model)
    flows = myresults["flow"]
    solph_representation.graph(
        flow_results=flows,
        path="tests/integration_tests/demands/test_gas_demand_results.png",
    )


test_basic_initialisation()
