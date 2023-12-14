from mtress.technologies import AirHeatExchanger


def test_air_heat_initialisation():
    ahe_name = "test_ahe"
    ahe_air_temperatures = 10  # °C
    ahe_nominal_power = 10e3  # W

    ahe = AirHeatExchanger(
        name=ahe_name,
        air_temperatures=ahe_air_temperatures,
        nominal_power=ahe_nominal_power,
    )

    assert ahe.name == ahe_name
    assert ahe.air_temperatures == ahe_air_temperatures
    assert ahe.nominal_power == ahe_nominal_power
