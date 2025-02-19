"""
Tests for the MTRESS heat storage.
"""

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
