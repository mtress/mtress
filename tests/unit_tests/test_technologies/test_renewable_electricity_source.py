from mtress.technologies import RenewableElectricitySource


def test_res_initialisation():
    name = "pv"
    nominal_power = 1
    specific_generation = [100e6, 200e6]
    working_rate = 10e-6
    fixed = True

    pv_source = RenewableElectricitySource(
        name=name,
        nominal_power=nominal_power,
        specific_generation=specific_generation,
        working_rate=working_rate,
        fixed=fixed,
    )

    assert pv_source.name == name == "pv"
    assert pv_source.nominal_power == nominal_power
    assert pv_source.specific_generation == specific_generation
    assert pv_source.working_rate == working_rate
    assert pv_source.fixed == fixed == True
