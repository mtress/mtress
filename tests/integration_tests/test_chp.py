import math
import pytest
import os
from oemof.solph import Results
from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress.technologies import SlackNode

from mtress.technologies._chp import CHPTemplate
from mtress.technologies import (
    CHP,
    OffsetCHP,
    # templates
    NATURALGAS_CHP,
    BIOGAS_CHP,
    BIOMETHANE_CHP,
    HYDROGEN_CHP,
    HYDROGEN_MIXED_CHP,
    NATURALGAS_MGT,
)
from pyomo.opt import SolverFactory

solver = "scip" if SolverFactory("scip").available() else "cbc"


class TestCHP:

    def check_chp_template(self, chp: CHP, template: CHPTemplate):

        assert chp.nominal_power == template.nominal_power
        assert (
            chp.nominal_electrical_efficiency
            == template.nominal_electrical_efficiency
        )
        assert (
            chp.nominal_thermal_efficiency
            == template.nominal_thermal_efficiency
        )
        assert chp.maximum_temperature == template.maximum_temperature
        assert chp.minimum_temperature == template.minimum_temperature
        assert chp.input_pressure == template.input_pressure
        assert chp.gas_type == template.gas_type
        assert type(chp.gas_type) is dict

    @pytest.mark.parametrize(
        "template, expected_result, allow_exports, tol",
        [
            # exports on @ net metering: electricity production is no problem
            (NATURALGAS_CHP, 0.8508048112500001, True, 1e-3),
            (BIOGAS_CHP, 1.6856640186499998, True, 1e-3),
            (BIOMETHANE_CHP, 0.7855700564999999, True, 1e-3),
            (HYDROGEN_CHP, 0.32534810449999996, True, 1e-3),
            (HYDROGEN_MIXED_CHP, 0.6803280214999999, True, 1e-3),
            (NATURALGAS_MGT, 0.7897307499999999, True, 1e-3),
            # exports off: electricity production determines the rest
            (NATURALGAS_CHP, 0.8508048112500001, False, 1e-3),
            (
                BIOGAS_CHP,
                1179261561.6128826,
                False,
                8.2,
            ),  # mismatched sup/dem!
            (BIOMETHANE_CHP, 0.7855700564999999, False, 1e-3),
            (HYDROGEN_CHP, 0.32534810449999996, False, 1e-3),
            (HYDROGEN_MIXED_CHP, 0.6803280214999999, False, 1e-3),
            (NATURALGAS_MGT, 0.7897307499999999, False, 1e-3),
        ],
    )
    def test_chp(
        self,
        template: CHPTemplate,
        expected_result: float,
        allow_exports: bool,
        tol,
    ):

        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(
            technologies.ElectricityGridConnection(
                working_rate=50e-6,
                revenue=50e-6 if allow_exports else None,
            )
        )

        house_1.add(
            carriers.GasCarrier(
                gases={
                    gas: [template.input_pressure]
                    for gas, share in template.gas_type.items()
                }
            )
        )
        for gas, share in template.gas_type.items():
            house_1.add(
                technologies.GasGridConnection(
                    gas_type=gas,
                    grid_pressure=template.input_pressure,
                    working_rate=5,
                )
            )

        house_1.add(
            carriers.HeatCarrier(
                temperature_levels=[20, template.maximum_temperature],
                # reference_temperature=10,
            )
        )
        house_1.add(SlackNode())

        chp = CHP(
            "chp", allow_electricity_feed_in=allow_exports, template=template
        )
        self.check_chp_template(chp, template)
        house_1.add(chp)

        # Add heat demands
        house_1.add(
            demands.FixedTemperatureHeating(
                name="heat_demand",
                min_flow_temperature=template.maximum_temperature,
                return_temperature=template.minimum_temperature,
                time_series=[1000],
            )
        )

        house_1.add(
            demands.Electricity(
                name="electricity_demand",
                time_series=[1000],
            )
        )

        solph_representation = SolphModel(
            energy_system,
            timeindex={
                "start": "2022-06-01 08:00:00",
                "end": "2022-06-01 09:00:00",
                "freq": "60T",
                "tz": "Europe/Berlin",
            },
        )

        solph_representation.build_solph_model()
        solved_model = solph_representation.solve(
            solver=solver, solve_kwargs={"tee": False}
        )
        mr = Results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=tol)


class TestOffsetCHP:

    def check_offset_chp_template(
        self,
        chp: CHP,
        template: CHPTemplate,
        normalised_min_load: float = None,
    ):

        if normalised_min_load is None:
            assert chp.normalised_min_load == template.normalised_min_load
        else:
            assert chp.normalised_min_load == normalised_min_load
        # assert chp.nominal_power == template.nominal_power
        assert (
            chp.nominal_electrical_efficiency
            == template.nominal_electrical_efficiency
        )
        assert (
            chp.nominal_thermal_efficiency
            == template.nominal_thermal_efficiency
        )
        assert (
            chp.min_load_electrical_efficiency
            == template.min_load_electrical_efficiency
        )
        assert (
            chp.min_load_thermal_efficiency
            == template.min_load_thermal_efficiency
        )
        assert chp.maximum_temperature == template.maximum_temperature
        assert chp.minimum_temperature == template.minimum_temperature
        assert chp.input_pressure == template.input_pressure
        assert chp.gas_type == template.gas_type
        assert type(chp.gas_type) is dict

    # *************************************************************************
    # *************************************************************************

    @pytest.mark.parametrize(
        "template, expected_result, normalised_min_load, allow_exports, tol",
        [
            # exports are not allowed: makes no difference because the
            # electrical loads match the nominal and minimum ones
            # ignore min load: should match results for CHP class
            (NATURALGAS_CHP, 0.9135757499999999, 0.0, False, 1e-3),
            (BIOGAS_CHP, 1.6128827000000001, 0.0, False, 1e-3),  #
            (BIOMETHANE_CHP, 0.8431486449, 0.0, False, 1e-3),
            (HYDROGEN_CHP, 0.38465384999999996, 0.0, True, 1e-3),
            (HYDROGEN_MIXED_CHP, 1.01719755, 0.0, False, 1e-3),
            (NATURALGAS_MGT, 1.30378095, 0.0, False, 1),
            # use min load from template (!= 0): penalties cannot be avoided
            (NATURALGAS_CHP, 28579735.004933327, None, False, 1),
            (BIOGAS_CHP, 25323091.774170972, None, False, 1),
            (BIOMETHANE_CHP, 28550544.92665914, None, False, 1),
            (HYDROGEN_CHP, 29909798.423119232, None, False, 1),
            (HYDROGEN_MIXED_CHP, 40666145.14604045, None, False, 1),
            (NATURALGAS_MGT, 14163710401.32201, None, False, 1),
            # exports on @ net metering: marginal impact due to huge penalties
            # min load = 0: no (major) penalties
            (NATURALGAS_CHP, 0.9135757499999999, 0.0, True, 1e-3),
            (BIOGAS_CHP, 1.6128827000000001, 0.0, True, 1e-3),  #
            (BIOMETHANE_CHP, 0.8431486449, 0.0, True, 1e-3),
            (HYDROGEN_CHP, 0.38465384999999996, 0.0, True, 1e-3),
            (HYDROGEN_MIXED_CHP, 1.01719755, 0.0, True, 1e-3),
            (NATURALGAS_MGT, 1.30378095, 0.0, True, 1),
            # use min load from template (!= 0): penalties cannot be avoided
            (NATURALGAS_CHP, 28579735.004933327, None, True, 1),
            (BIOGAS_CHP, 25323091.774170972, None, True, 1),
            (BIOMETHANE_CHP, 28550544.92665914, None, True, 1),
            (HYDROGEN_CHP, 29909798.423119232, None, True, 1),
            (HYDROGEN_MIXED_CHP, 40666145.14604045, None, True, 1),
            (NATURALGAS_MGT, 143067784.023681, None, True, 1),
        ],
    )
    def test_min_power(
        self,
        template: CHPTemplate,
        expected_result: float,
        normalised_min_load: float,
        allow_exports: bool,
        tol,
    ):

        nominal_power = 1000
        normalised_min_load = (
            template.normalised_min_load
            if normalised_min_load is None
            else 0.0
        )

        max_fuel_power = nominal_power / template.nominal_electrical_efficiency
        min_fuel_power = max_fuel_power * normalised_min_load
        max_heat_power = max_fuel_power * template.nominal_thermal_efficiency
        min_heat_power = min_fuel_power * template.min_load_thermal_efficiency
        max_elec_power = nominal_power
        min_elec_power = (
            min_fuel_power * template.min_load_electrical_efficiency
        )

        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(
            technologies.ElectricityGridConnection(
                working_rate=50e-6, revenue=50e-6 if allow_exports else None
            )
        )

        house_1.add(
            carriers.GasCarrier(
                gases={
                    gas: [template.input_pressure]
                    for gas, share in template.gas_type.items()
                }
            )
        )
        for gas, share in template.gas_type.items():
            house_1.add(
                technologies.GasGridConnection(
                    gas_type=gas,
                    grid_pressure=template.input_pressure,
                    working_rate=5,
                )
            )

        house_1.add(
            carriers.HeatCarrier(
                temperature_levels=[20, template.maximum_temperature],
                # reference_temperature=10,
            )
        )
        #
        house_1.add(SlackNode())

        chp = OffsetCHP(
            "chp",
            nominal_power=nominal_power,
            allow_electricity_feed_in=allow_exports,
            normalised_min_load=normalised_min_load,
            template=template,
        )
        house_1.add(chp)

        # Add heat demands
        house_1.add(
            demands.FixedTemperatureHeating(
                name="heat_demand",
                min_flow_temperature=template.maximum_temperature,
                return_temperature=template.minimum_temperature,
                time_series=[
                    max_heat_power,
                    # the factor 0.99 is meant to force a demand below the min.
                    min_heat_power * 0.99,
                ],
            )
        )

        house_1.add(
            demands.Electricity(
                name="electricity_demand",
                time_series=[max_elec_power, min_elec_power],
            )
        )

        solph_representation = SolphModel(
            energy_system,
            timeindex={
                "start": "2022-06-01 08:00:00",
                "end": "2022-06-01 10:00:00",
                "freq": "60T",
                "tz": "Europe/Berlin",
            },
        )

        solph_representation.build_solph_model()
        solved_model = solph_representation.solve(
            solver=solver, solve_kwargs={"tee": False}
        )
        mr = Results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=tol)

    # *************************************************************************
    # *************************************************************************

    @pytest.mark.parametrize(
        "template, load_multiplier, expected_result, tol",
        [
            # reference: nominal power matches demand
            (NATURALGAS_CHP, 1, 0.09135757400000062, 1e-3),
            # maximum power cannot be exceeded, nominal production + imports
            (
                NATURALGAS_CHP,
                1.5,
                0.09135757400000062
                + NATURALGAS_CHP.nominal_power * 0.5 * 50e-6,
                1e-3,
            ),
            # CHP cannot be used, electricity must be imported
            (
                NATURALGAS_CHP,
                0.05,
                NATURALGAS_CHP.nominal_power * 0.05 * 50e-6,
                1e-3,
            ),
            # CHP cannot be used, electricity must be imported
            (
                NATURALGAS_CHP,
                0.099,
                NATURALGAS_CHP.nominal_power * 0.099 * 50e-6,
                1e-3,
            ),
        ],
    )
    def test_power_limits(
        self, template, load_multiplier, expected_result, tol
    ):

        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(
            technologies.ElectricityGridConnection(
                working_rate=50e-6, revenue=50e-6
            )
        )

        house_1.add(
            carriers.GasCarrier(
                gases={
                    gas: [template.input_pressure]
                    for gas, share in template.gas_type.items()
                }
            )
        )

        house_1.add(
            carriers.HeatCarrier(
                temperature_levels=[
                    template.minimum_temperature,
                    template.maximum_temperature,
                ],
                # reference_temperature=10,
                # heat does not matter
                # missing_heat_penalty=0,
                # excess_heat_penalty=0
            )
        )

        house_1.add(
            SlackNode(
                {
                    carriers.HeatCarrier: 0.0,
                    # carriers.GasCarrier: 1e9,
                    # carriers.ElectricityCarrier: 1e9
                }
            )
        )

        chp = OffsetCHP(
            name="chp", allow_electricity_feed_in=False, template=template
        )
        house_1.add(chp)

        for gas, share in template.gas_type.items():
            house_1.add(
                technologies.GasGridConnection(
                    gas_type=gas,
                    grid_pressure=template.input_pressure,
                    working_rate=1e-3,
                )
            )

        # Add heat demands
        house_1.add(
            demands.FixedTemperatureHeating(
                name="heat_demand",
                min_flow_temperature=template.maximum_temperature,
                return_temperature=template.minimum_temperature,
                time_series=[template.nominal_power / 2],
            )
        )

        house_1.add(
            demands.Electricity(
                name="electricity_demand",
                time_series=[template.nominal_power * load_multiplier],
            )
        )

        solph_representation = SolphModel(
            energy_system,
            timeindex={
                "start": "2022-06-01 08:00:00",
                "end": "2022-06-01 09:00:00",
                "freq": "60T",
                "tz": "Europe/Berlin",
            },
        )

        solph_representation.build_solph_model()
        solved_model = solph_representation.solve(
            solver=solver, solve_kwargs={"tee": False}
        )
        mr = Results(solved_model)
        # print(expected_result-mr["objective"])
        assert math.isclose(expected_result, mr["objective"], abs_tol=tol)

    # *************************************************************************
    # *************************************************************************

    @pytest.mark.parametrize(
        "thermal_efficiency_variation, "
        + "electrical_efficiency_variation, "
        + "test_factor, "
        + "expected_result, "
        + "tol",
        [
            # constant thermal efficiency, constant electrical efficiency
            # - same performance on both time steps
            (0.0, 0.0, 1, -1098.73620879, 1e-3),
            # - penalties on second time step because load is too low
            (0.0, 0.0, 0.99, 34073353.26379121, 1),
            # constant thermal efficiency, increasing electrical efficiency
            # - higher (worse) result because efficiency is reduced at low load
            (0.0, -0.05, 1, -1098.7186080557, 1e-3),
            # - higher (worse) result because efficiency is reduced at low load
            (0.0, -0.05, 0.99, 34073353.28139195, 1),
            # constant thermal efficiency, decreasing electrical efficiency
            # - better results due to higher elec. efficiency at low load
            (0.0, 0.05, 1, -1098.7492307695002, 1e-3),
            # - better results due to higher electric. efficiency at low load
            (0.0, 0.05, 0.99, 34073353.25076923, 1),
            # increasing thermal efficiency, constant electrical efficiency
            # - same results since production matches demand
            (-0.05, 0.0, 1, -1098.73620879, 1e-3),
            # - penalties are lower since load is lower
            (-0.05, 0.0, 0.99, 30287303.26379121, 1),
            # decreasing thermal efficiency, constant electrical efficiency
            # - same results since production matches demand
            (0.05, 0.0, 1, -1098.73620879, 1e-3),
            # - penalties are higher since load is higher
            (0.05, 0.0, 0.99, 37859403.26379121, 1),
            # varying thermal and electrical efficiencies
            # thermal efficiency increases, electrical efficiency increases
            (-0.05, -0.05, 1, -1098.7186080557, 1e-3),
            (-0.05, -0.05, 0.99, 30287303.281391945, 1),
            # thermal efficiency decreases, electrical efficiency increases
            (0.05, -0.05, 1, -1098.7186080557, 1e-3),
            (0.05, -0.05, 0.99, 37859403.28139195, 1),
            # thermal efficiency increases, electrical efficiency decreases
            (-0.05, 0.05, 1, -1098.7492307695002, 1e-3),
            (-0.05, 0.05, 0.99, 30287303.25076923, 1),
            # thermal efficiency decreases, electrical efficiency decreases
            (0.05, 0.05, 1, -1098.7492307695002, 1e-3),
            (0.05, 0.05, 0.99, 37859403.25076923, 1),
        ],
    )
    def test_variable_efficiency(
        self,
        thermal_efficiency_variation: float,
        electrical_efficiency_variation: float,
        test_factor: float,
        expected_result: float,
        tol: float,
    ):

        # test details:
        # - electrical loads are always set to the respect. nominal and minimum
        # - a test factor of 1 requires exactly the nominal and minimum thermal
        # loads;
        # - a test factor below 1 requires less than the minimum thermal load,
        # prompting penalties, since the unit is forced to produce extra heat
        # - export prices are deliberately attractive so as not to create elec.
        # load problems (loads are met through imports, exports gen. revenue)
        # - the nominal thermal and electrical efficincies are kept constant
        # since they determine the size of the loads (changing them would make
        # interpreting the results harder)
        # - runs with a test factor of 1 cannot have penalties and the
        # differences reflect the impact of the minimum load perfomance differ.

        nominal_thermal_efficiency = 0.45
        nominal_electrical_efficiency = 0.35
        min_load_thermal_efficiency = (
            nominal_thermal_efficiency + thermal_efficiency_variation
        )
        min_load_electrical_efficiency = (
            nominal_electrical_efficiency + electrical_efficiency_variation
        )

        allow_exports = True
        template = NATURALGAS_CHP
        # the nominal (electrical) power is set to 1000 to simplify the analys.
        nominal_power = 1000

        price_imp_elec = 50e-6
        price_exp_elec = 1  # exporting is the priority
        price_imp_gas = 5

        max_fuel_power = nominal_power / nominal_electrical_efficiency
        min_fuel_power = max_fuel_power * template.normalised_min_load
        max_heat_power = max_fuel_power * nominal_thermal_efficiency
        min_heat_power = min_fuel_power * min_load_thermal_efficiency
        max_elec_power = nominal_power
        min_elec_power = min_fuel_power * min_load_electrical_efficiency

        # *********************************************************************

        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(
            technologies.ElectricityGridConnection(
                working_rate=price_imp_elec,
                revenue=price_exp_elec if allow_exports else None,
            )
        )

        house_1.add(
            carriers.GasCarrier(
                gases={
                    gas_label: [template.input_pressure]
                    for gas_label, gas in template.gas_type.items()
                }
            )
        )
        for gas, share in template.gas_type.items():
            house_1.add(
                technologies.GasGridConnection(
                    gas_type=gas,
                    grid_pressure=template.input_pressure,
                    working_rate=price_imp_gas,
                )
            )

        house_1.add(
            carriers.HeatCarrier(
                temperature_levels=[
                    template.minimum_temperature,
                    template.maximum_temperature,
                ],
                # reference_temperature=10,
            )
        )
        #
        house_1.add(SlackNode())

        chp = OffsetCHP(
            name="chp",
            nominal_power=nominal_power,
            allow_electricity_feed_in=allow_exports,
            # override template
            nominal_electrical_efficiency=nominal_electrical_efficiency,
            nominal_thermal_efficiency=nominal_thermal_efficiency,
            min_load_electrical_efficiency=min_load_electrical_efficiency,
            min_load_thermal_efficiency=min_load_thermal_efficiency,
            template=template,
        )
        house_1.add(chp)

        # Add heat demands
        house_1.add(
            demands.FixedTemperatureHeating(
                name="heat_demand",
                min_flow_temperature=template.maximum_temperature,
                return_temperature=template.minimum_temperature,
                time_series=[
                    max_heat_power,
                    # the test factor is meant to adjust the demand
                    min_heat_power * test_factor,
                ],
            )
        )

        house_1.add(
            demands.Electricity(
                name="electricity_demand",
                time_series=[max_elec_power, min_elec_power],
            )
        )

        solph_representation = SolphModel(
            energy_system,
            timeindex={
                "start": "2022-06-01 08:00:00",
                "end": "2022-06-01 10:00:00",
                "freq": "60T",
                "tz": "Europe/Berlin",
            },
        )

        solph_representation.build_solph_model()
        solved_model = solph_representation.solve(
            solver=solver, solve_kwargs={"tee": False}
        )
        mr = Results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=tol)


# *****************************************************************************
# *****************************************************************************
