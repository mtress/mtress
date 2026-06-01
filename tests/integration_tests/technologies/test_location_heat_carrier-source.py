# -*- coding: utf-8 -*-

from mtress import Location
from mtress.carriers import HeatCarrier
from mtress.technologies import HeatSource
from mtress import EnergyType

def test_establish_interconnections():
    location = Location(label="location")

    temperatures = [-10, 10, 35, 75, 80]
    hc = location.subnode(
        HeatCarrier,
        local_name="heat",
        temperature_levels=temperatures,
    )

    reservoir_temperature = [0, 15, 55, -8.5]
    nominal_power = 10000

    src = location.subnode(
        HeatSource,
        local_name="source",
        reservoir_temperature=reservoir_temperature,
        nominal_power=nominal_power,
        minimum_working_temperature=0,
        maximum_working_temperature=40,
    )

    hc.establish_interconnections()

    # preliminary temperatures are not taken
    assert hc.levels == temperatures

