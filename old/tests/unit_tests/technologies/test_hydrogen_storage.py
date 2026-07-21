from mtress.physics import HYDROGEN, calc_hydrogen_density
from mtress.technologies import H2Storage
from mtress.technologies._abstract_homogenous_storage import Implementation


def test_h2_storage():
    storage_name = "h2_storage"
    storage_volume = 0.8
    storage_power_limit = 2
    pressure = 100

    storage = H2Storage(
        name=storage_name,
        volume=storage_volume,
        power_limit=storage_power_limit,
    )

    assert storage.name == storage_name
    assert storage.volume == storage_volume
    assert storage.power_limit == storage_power_limit
    assert storage.gas_type == HYDROGEN
    assert storage.implementation == Implementation.STRICT
    assert (
        storage._storage_content(pressure=pressure)
        == calc_hydrogen_density(pressure=pressure) * storage_volume
    )

    assert storage.calc_density(pressure=pressure) == calc_hydrogen_density(
        pressure=pressure
    )
