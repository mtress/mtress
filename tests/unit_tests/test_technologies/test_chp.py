from mtress.technologies import CHP, NATURALGAS_CHP
from mtress.physics import NATURAL_GAS


def test_fuelcell():
    chp_name = ("CHP",)
    chp_nominal_power = (100e3)

    # Considering NATURALGAS_CHP template type
    chp = CHP(
        name=chp_name,
        nominal_power=chp_nominal_power,
        template=NATURALGAS_CHP,
    )

    assert chp.name == chp_name
    assert chp.nominal_power == chp_nominal_power
    assert chp.electric_efficiency == NATURALGAS_CHP.electric_efficiency
    assert chp.thermal_efficiency == NATURALGAS_CHP.thermal_efficiency
    assert chp.maximum_temperature == NATURALGAS_CHP.maximum_temperature == 85
    assert chp.input_pressure == NATURALGAS_CHP.input_pressure == 1
    assert chp.gas_type == {NATURAL_GAS: 1}
    assert type(chp.gas_type) == dict
