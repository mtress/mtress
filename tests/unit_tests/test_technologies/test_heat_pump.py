from mtress.technologies import HeatPump


def test_heat_pump_initialisation():
    hp_name = "test_hp"
    hp_thermal_power_limit = 5e3  # W
    hp_cop_0_35 = 4.6
    hp_anergy_soruces = None

    hp = HeatPump(
        name=hp_name,
        thermal_power_limit=hp_thermal_power_limit,
        cop_0_35=hp_cop_0_35,
        anergy_sources=hp_anergy_soruces,
    )

    assert hp.name == hp_name
    assert hp.thermal_power_limit == hp_thermal_power_limit
    assert hp.cop_0_35 == hp_cop_0_35
    assert hp.anergy_sources == hp_anergy_soruces
