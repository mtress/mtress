from mtress.technologies import HeatExchanger


def test_air_heat_initialisation():
    ahe_name = "test_ahe"
    ahe_air_temperatures = 10  # °C
    ahe_nominal_power = 10e3  # W

    ahe = HeatExchanger(
        name=ahe_name,
        reservoir_temperature=ahe_air_temperatures,
        nominal_power=ahe_nominal_power,
    )

    assert ahe.name == ahe_name
    assert ahe.reservoir_temperature == ahe_air_temperatures
    assert ahe.nominal_power == ahe_nominal_power
