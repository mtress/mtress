from mtress.technologies import Slack
from mtress import carriers

import pytest


def test_slack_penalty():
    slack = Slack()
    assert slack.penalty == 1e9

    slack = Slack(10)
    assert slack.penalty == 10

    penalty = {carriers.ElectricityCarrier: 1e5, carriers.HeatCarrier: 1e7}
    slack = Slack(penalty)
    assert type(slack.penalty) == dict
    assert slack.penalty == penalty

    with pytest.raises(ValueError):
        penalty = {
            carriers.ElectricityCarrier: "banana",
            carriers.HeatCarrier: 1e7,
        }
        Slack(penalty)
