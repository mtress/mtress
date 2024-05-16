from mtress.technologies import ElectricityGridConnection


def test_grid_initialisation():
    grid_working_rate = None
    grid_demand_rate = None

    grid = ElectricityGridConnection(
        working_rate=grid_working_rate,
        demand_rate=grid_demand_rate,
    )

    assert grid.working_rate == grid_working_rate
    assert grid.demand_rate == grid_demand_rate
