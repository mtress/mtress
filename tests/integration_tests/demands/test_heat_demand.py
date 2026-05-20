from oemof.solph import Results

from mtress import Location, MetaModel, SolphModel, _carriers, demands


def test_basic_initialisation():

    energy_system = MetaModel()

    loc = Location("house")

    energy_system.add_location(loc)

    hc = _carriers.HeatCarrier(location=loc)

    hd = demands.FixedTemperatureHeating(
        "heating_demand",
        min_flow_temperature=35,
        return_temperature=20,
        time_series=[1, 2, 3],
        location=loc,
    )
    assert hd.label == ("heating_demand", "house")
    assert hd.parent == loc
    assert hd._time_series == [1, 2, 3]

    assert len(hd.inbound_interfaces) == 0
    assert len(hd.outbound_interfaces) == 1

    cd = demands.FixedTemperatureCooling(
        "cooling_demand",
        max_flow_temperature=20,
        return_temperature=30,
        time_series=[1, 2, 3],
        location=loc,
    )
    assert cd.label == ("cooling_demand", "house")
    assert cd.parent == loc
    assert cd._time_series == [1, 2, 3]

    assert len(cd.inbound_interfaces) == 0
    assert len(cd.outbound_interfaces) == 1

    solph_representation = SolphModel(
        energy_system,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 02:00:00",
            "freq": "60min",
        },
    )

    solph_representation.graph(
        path="tests/integration_tests/demands/test_heat_demand.png"
    )

    solved_model = solph_representation.solve(solve_kwargs={"tee": False})

    myresults = Results(solved_model)
    flows = myresults["flow"]
    solph_representation.graph(
        flow_results=flows,
        path="tests/integration_tests/demands/test_heat_demand_results.png",
    )


test_basic_initialisation()
