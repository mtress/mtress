from mtress.technologies import SlackNode
from mtress import MetaModel, Location, SolphModel, carriers, demands
from mtress.physics import HYDROGEN

import pytest


def test_slack_penalty():
    slack = SlackNode()
    assert slack.penalty == 1e9

    slack = SlackNode(10)
    assert slack.penalty == 10

    penalty = {carriers.ElectricityCarrier: 1e5, carriers.HeatCarrier: 1e7}
    slack = SlackNode(penalty)
    assert type(slack.penalty) == dict
    assert slack.penalty == penalty

    with pytest.raises(ValueError):
        penalty = {
            carriers.ElectricityCarrier: "banana",
            carriers.HeatCarrier: 1e7,
        }
        SlackNode(penalty)


def test_slack_build():
    # test default slack
    meta_model1 = MetaModel()
    location1 = Location(name="location1")
    meta_model1.add_location(location1)

    location1.add(carriers.ElectricityCarrier())
    location1.add(
        demands.Electricity(name="electricity_demand1", time_series=[0, 1, 2])
    )
    location1.add(SlackNode())

    solph_representation1 = SolphModel(
        meta_model1,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 03:00:00",
            "freq": "60T",
        },
    )

    solph_representation1.build_solph_model()

    # test specific slack for every carrier
    meta_model2 = MetaModel()
    location2 = Location(name="location2")
    meta_model2.add_location(location2)

    location2.add(carriers.ElectricityCarrier())
    location2.add(
        demands.Electricity(name="electricity_demand2", time_series=[0, 1, 2])
    )

    location2.add(
        carriers.HeatCarrier(
            temperature_levels=[10, 20], reference_temperature=0
        )
    )
    location2.add(
        demands.FixedTemperatureHeating(
            name="heat_demand2",
            min_flow_temperature=20,
            return_temperature=10,
            time_series=[1, 2, 3],
        )
    )

    location2.add(carriers.GasCarrier(gases={HYDROGEN: [30]}))
    location2.add(
        demands.GasDemand(
            name="H2_demand",
            gas_type=HYDROGEN,
            time_series=[0.5, 1.0, 1.5],
            pressure=30,
        )
    )

    location2.add(
        SlackNode(
            {
                carriers.ElectricityCarrier: 1e3,
                carriers.HeatCarrier: 1e5,
                carriers.GasCarrier: 1e7,
            }
        )
    )

    solph_representation2 = SolphModel(
        meta_model2,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 03:00:00",
            "freq": "60T",
        },
    )

    solph_representation2.build_solph_model()
