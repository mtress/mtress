from mtress.technologies import Photovoltaics


def test_pv_initialisation():
    pv_name = "test_pv"
    pv_location = (52.729, 8.181)
    pv_nominal_power = 500  # Wp
    pv_weather = {}
    pv_surface_azimuth = 180
    pv_surface_tilt = 35
    pv_fixed = True

    pv = Photovoltaics(
        name=pv_name,
        location=pv_location,
        nominal_power=pv_nominal_power,
        weather=pv_weather,
        surface_azimuth=pv_surface_azimuth,
        surface_tilt=pv_surface_tilt,
        fixed=pv_fixed,
    )

    assert pv.name == pv_name
    assert pv.geo_location.latitude == pv_location[0]
    assert pv.geo_location.longitude == pv_location[1]
    assert pv.nominal_power == pv_nominal_power
    assert pv.weather == pv_weather
    assert pv.surface_azimuth == pv_surface_azimuth
    assert pv.surface_tilt == pv_surface_tilt
    assert pv.fixed == pv_fixed
