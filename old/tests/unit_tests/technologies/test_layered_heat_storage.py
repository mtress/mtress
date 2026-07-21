"""
Tests for the MTRESS heat storage.
"""

from oemof import solph
import pytest

from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)

from mtress.technologies import LayeredHeatStorage


def test_heat_carrier_initilisation():

    hs_args = {
        "name": "storage",
        "diameter": 1,
        "volume": 1,
        "power_limit": 1e6,  # 1 MW
        "ambient_temperature": [0, 0],
    }

    hs = LayeredHeatStorage(**hs_args)

    for k, v in hs_args.items():
        assert getattr(hs, k) == v


@pytest.mark.skip(reason="Not really a test, yet.")
def test_layered_heat_losses():
    N_DAYS = 7

    house_1 = Location(name="house_1")
    house_1.add(
        carriers.HeatCarrier(
            temperature_levels=[10, 20, 30],
        )
    )
    house_1.add(
        technologies.LayeredHeatStorage(
            name="HS",
            diameter=1,
            volume=10,
            ambient_temperature=N_DAYS * 24 * [0],
            power_limit=None,
            max_temperature=30,
            min_temperature=20,
            initial_storage_levels={30: 0.25},
            balanced=False,
        )
    )
    meta_model = MetaModel(locations=[house_1])

    solph_representation = SolphModel(
        meta_model=meta_model,
        timeindex={
            "start": "2021-01-01 00:00:00",
            "end": f"2021-01-{N_DAYS+1} 00:00:00",
            "freq": "60min",
        },
    )

    solph_representation.build_solph_model()

    solved_model = solph_representation.solve(solve_kwargs={"tee": False})
    myresults = solph.processing.results(solved_model)

    return myresults


if __name__ == "__main__":
    results = test_layered_heat_losses()

    for key, result in results.items():
        if key[1] is None:
            print(result)
