from mtress.technologies import Electrolyser, ALKALINE_ELECTROLYSER


def test_electrolyser():
    ely_name = "AEL",
    ely_nominal_power = 100e3,

    electrolyser = Electrolyser(
        name=ely_name,
        nominal_power=ely_nominal_power,
        template=ALKALINE_ELECTROLYSER,
    )

    assert electrolyser.name == ely_name
    assert electrolyser.nominal_power == ely_nominal_power
    assert electrolyser.hydrogen_efficiency == ALKALINE_ELECTROLYSER.hydrogen_efficiency
    assert electrolyser.thermal_efficiency == ALKALINE_ELECTROLYSER.thermal_efficiency
    assert (
        electrolyser.maximum_temperature
        == ALKALINE_ELECTROLYSER.maximum_temperature
    )
    assert (
        electrolyser.hydrogen_output_pressure
        == ALKALINE_ELECTROLYSER.hydrogen_output_pressure
        == 30
    )

