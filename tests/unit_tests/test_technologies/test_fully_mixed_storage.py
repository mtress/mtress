from mtress.physics import H2O_DENSITY, H2O_HEAT_CAPACITY, SECONDS_PER_HOUR
from mtress.technologies import FullyMixedHeatStorage

def test_storage_initialisation():
    storage_diameter = 0.5
    storage_volume = 0.8
    storage_power_limit = 2
    ambient_temperature = 10
    
    storage = FullyMixedHeatStorage(
        name="test_storage",
        diameter=storage_diameter,
        volume=storage_volume,
        power_limit=storage_power_limit,
        ambient_temperature=ambient_temperature,
    )

    assert storage.diameter == storage_diameter
    assert storage.volume == storage_volume
    assert storage.power_limit == storage_power_limit
    assert storage.ambient_temperature == ambient_temperature
    assert storage.capacity_per_unit == storage_volume * (H2O_DENSITY * H2O_HEAT_CAPACITY) / SECONDS_PER_HOUR
