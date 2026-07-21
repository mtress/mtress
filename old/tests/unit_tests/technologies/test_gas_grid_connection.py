from mtress.physics import HYDROGEN, NATURAL_GAS
from mtress.technologies import GasGridConnection


def test_gas_grid_initialisation():
    gas_grid_name = "test_gas_grid"
    gas_type = HYDROGEN
    gas_grid_pressure = 30
    gas_working_rate = 15

    gas_grid = GasGridConnection(
        name=gas_grid_name,
        gas_type=gas_type,
        grid_pressure=gas_grid_pressure,
        working_rate=gas_working_rate,
    )

    assert (
        gas_grid.name == "GasGridConnection"
    )  # TODO: gas_grid.name == gas_grid_name
    assert gas_grid.gas_type == gas_type
    assert gas_grid.grid_pressure == gas_grid_pressure
    assert gas_grid.working_rate == gas_working_rate

    gas_type = NATURAL_GAS
    gas_grid = GasGridConnection(
        name=gas_grid_name,
        gas_type=gas_type,
        grid_pressure=gas_grid_pressure,
        working_rate=gas_working_rate,
    )
    assert gas_grid.gas_type == gas_type
