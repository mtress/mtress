import math
import pytest
import os
from oemof.solph.processing import meta_results
from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)

# from mtress.physics import NATURAL_GAS, BIOGAS, BIO_METHANE, HYDROGEN
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
    AET100NG_CHP
)


class TestCHP:

    def check_chp_template(self, chp: CHP, template: CHPTemplate):

        assert chp.nominal_power == template.nominal_power
        assert ( 
            chp.nominal_electrical_efficiency == 
            template.nominal_electrical_efficiency
            )
        assert ( 
            chp.nominal_thermal_efficiency == 
            template.nominal_thermal_efficiency
            )
        assert chp.maximum_temperature == template.maximum_temperature
        assert chp.minimum_temperature == template.minimum_temperature
        assert chp.input_pressure == template.input_pressure
        assert chp.gas_type == template.gas_type
        assert type(chp.gas_type) is dict

    @pytest.mark.parametrize(
        "template, expected_result, allow_exports",
        [
            # exports on @ net metering
            (NATURALGAS_CHP, 0.8508048112500001, True),
            (BIOGAS_CHP, 1.6856640186499998, True),
            (BIOMETHANE_CHP, 0.7855700564999999, True),
            (HYDROGEN_CHP, 0.32534810449999996, True),
            (HYDROGEN_MIXED_CHP, 0.6963973715, True),
            (AET100NG_CHP, 0.8077001939999999, True),
            # exports off: changes outcome when the electrical eff. is higher
            (NATURALGAS_CHP, 0.8508048112500001, False),
            (BIOGAS_CHP, 58187714401.612885, False), # mismatched production!
            (BIOMETHANE_CHP, 0.7855700564999999, False),
            (HYDROGEN_CHP, 0.32534810449999996, False),
            (HYDROGEN_MIXED_CHP, 0.6963973715, False),
            (AET100NG_CHP, 0.8077001939999999, False),
        ],
    )
    def test_chp(
            self, 
            template: CHPTemplate, 
            expected_result: float,
            allow_exports: bool
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
                reference_temperature=10,
            )
        )

        chp = CHP(
            "chp", 
            allow_electricity_feed_in=allow_exports,
            template=template
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
        solved_model = solph_representation.solve(solve_kwargs={"tee": False})
        mr = meta_results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)
        
class TestOffsetCHP:

    def check_offset_chp_template(
            self, 
            chp: CHP,
            template: CHPTemplate,
            normalised_min_load: float = None
            ):
        
        if normalised_min_load is None:
            assert chp.normalised_min_load == template.normalised_min_load
        else: 
            assert chp.normalised_min_load == normalised_min_load
        # assert chp.nominal_power == template.nominal_power
        assert (
            chp.nominal_electrical_efficiency == 
            template.nominal_electrical_efficiency
            )
        assert (
            chp.nominal_thermal_efficiency == 
            template.nominal_thermal_efficiency
            )
        assert (
            chp.min_load_electrical_efficiency == 
            template.min_load_electrical_efficiency
            )
        assert (
            chp.min_load_thermal_efficiency == 
            template.min_load_thermal_efficiency
            )
        assert chp.maximum_temperature == template.maximum_temperature
        assert chp.minimum_temperature == template.minimum_temperature
        assert chp.input_pressure == template.input_pressure
        assert chp.gas_type == template.gas_type
        assert type(chp.gas_type) is dict
    
    # *************************************************************************
    # *************************************************************************
    
    @pytest.mark.parametrize(
        "template, expected_result, normalised_min_load, allow_exports",
        [
            # exports are not allowed: makes no difference because the 
            # electrical loads match the nominal and minimum ones
            # ignore min load: should match results for CHP class
            (NATURALGAS_CHP, 0.9185757499999999, 0.0, False),
            (BIOGAS_CHP, 1.6178827, 0.0, False), # 
            (BIOMETHANE_CHP, 0.8481486449, 0.0, False),
            (HYDROGEN_CHP, 0.38965384999999997, 0.0, True),
            (HYDROGEN_MIXED_CHP, 1.04685495, 0.0, False),
            (AET100NG_CHP, 1.3688843499999999, 0.0, False),
            # # use min load from template (!= 0): penalties cannot be avoided
            (NATURALGAS_CHP, 1410195551.004933, None, False),
            (BIOGAS_CHP, 1249504641.7741709, None, False),
            (BIOMETHANE_CHP, 1408755200.926659, None, False),
            (HYDROGEN_CHP, 1562637370.4231193, None, False),
            (HYDROGEN_MIXED_CHP, 2006569161.1460404, None, False),
            (AET100NG_CHP, 2119385291.500273, None, False),
            # exports on @ net metering: marginal impact due to huge penalties
            # min load = 0: no (major) penalties
            (NATURALGAS_CHP, 0.9185757499999999, 0.0, True),
            (BIOGAS_CHP, 1.6178827, 0.0, True), # 
            (BIOMETHANE_CHP, 0.8481486449, 0.0, True),
            (HYDROGEN_CHP, 0.38965384999999997, 0.0, True),
            (HYDROGEN_MIXED_CHP, 1.04685495, 0.0, True),
            (AET100NG_CHP, 1.3688843499999999, 0.0, True),
            # use min load from template (!= 0): penalties cannot be avoided
            (NATURALGAS_CHP, 1410195551.004933, None, True),
            (BIOGAS_CHP, 1249504641.7741709, None, True),
            (BIOMETHANE_CHP, 1408755200.926659, None, True),
            (HYDROGEN_CHP, 1562637370.4231193, None, True),
            (HYDROGEN_MIXED_CHP, 2006569161.1460404, None, True),
            (AET100NG_CHP, 2119385291.500273, None, True),
        ],
    )
    def test_min_power(
            self,
            template: CHPTemplate, 
            expected_result: float, 
            normalised_min_load: float,
            allow_exports: bool
            ):

        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(
            technologies.ElectricityGridConnection(
                working_rate=50e-6,
                revenue=50e-6 if allow_exports else None
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
                reference_temperature=10,
            )
        )
        # 
        nominal_power = 1000
        normalised_min_load = ( 
            template.normalised_min_load 
            if normalised_min_load is None else 
            0.0
            )
        chp = OffsetCHP(
            "chp", 
            nominal_power=nominal_power,
            allow_electricity_feed_in=allow_exports,
            normalised_min_load=normalised_min_load,
            template=template
            )
        house_1.add(chp)

        # Add heat demands
        house_1.add(
            demands.FixedTemperatureHeating(
                name="heat_demand",
                min_flow_temperature=template.maximum_temperature,
                return_temperature=template.minimum_temperature,
                time_series=[
                    (nominal_power/template.nominal_electrical_efficiency)*
                    template.nominal_thermal_efficiency,
                    # the factor 0.99 is meant to force a demand below the min.
                    (nominal_power*normalised_min_load/
                      template.min_load_electrical_efficiency)*
                    template.min_load_thermal_efficiency*0.99,
                    ],
            )
        )
        
        house_1.add(
            demands.Electricity(
                name="electricity_demand",
                time_series=[
                    nominal_power, 
                    nominal_power*template.normalised_min_load
                    ],
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
        solved_model = solph_representation.solve(solve_kwargs={"tee": False})
        mr = meta_results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)
    
    # *************************************************************************
    # *************************************************************************
        
    # @pytest.mark.parametrize(
    #     "nominal_thermal_efficiency, " +
    #     "min_load_thermal_efficiency, "+
    #     "nominal_electrical_efficiency, "+
    #     "min_load_electrical_efficiency, "+
    #     "test_factor, "+
    #     "expected_result",
    #     [
    #         # constant thermal efficiency, constant electrical efficiency
    #         (0.45, 0.45, 0.35, 0.35, 1.5, 34),
    #         (0.45, 0.45, 0.35, 0.35, 0.99, 34),
    #         # thermal efficiency increases, electrical efficiency increases
    #         # (0.4, 0.45, 0.3, 0.35, 1.45, 34),
    #         # (0.4, 0.45, 0.3, 0.35, 0.99, 34),
    #         # thermal efficiency decreases, electrical efficiency increases
    #         # (0.45, 0.35, 0.3, 0.35, 1.45, 34),
    #         # (0.45, 0.35, 0.3, 0.35, 0.99, 34),
    #         # thermal efficiency increases, electrical efficiency decreases
    #         # thermal efficiency decreases, electrical efficiency decreases
    #     ],
    # )
    # def test_variable_efficiency(
    #         self,
    #         nominal_thermal_efficiency: float,
    #         min_load_thermal_efficiency: float,
    #         nominal_electrical_efficiency: float,
    #         min_load_electrical_efficiency: float,
    #         test_factor: float,
    #         expected_result: float
    #         ):
        
    #     allow_exports = True
    #     template = NATURALGAS_CHP
        

    #     os.chdir(os.path.dirname(__file__))
    #     energy_system = MetaModel()
    #     house_1 = Location(name="house_1")
    #     energy_system.add_location(house_1)

    #     house_1.add(carriers.ElectricityCarrier())
    #     house_1.add(
    #         technologies.ElectricityGridConnection(
    #             working_rate=50e-6,
    #             revenue=50e-6 if allow_exports else None
    #             )
    #         )

    #     house_1.add(
    #         carriers.GasCarrier(
    #             gases={
    #                 gas_label: [template.input_pressure]
    #                 for gas_label, gas in template.gas_type.items()
    #             }
    #         )
    #     )
    #     for gas, share in template.gas_type.items():
    #         house_1.add(
    #             technologies.GasGridConnection(
    #                 gas_type=gas,
    #                 grid_pressure=template.input_pressure,
    #                 working_rate=5,
    #             )
    #         )

    #     house_1.add(
    #         carriers.HeatCarrier(
    #             temperature_levels=[
    #                 template.minimum_temperature, 
    #                 template.maximum_temperature
    #                 ],
    #             reference_temperature=template.minimum_temperature-10,
    #         )
    #     )
    #     # 
    #     nominal_power = 1000
    #     chp = OffsetCHP(
    #         name="chp", 
    #         nominal_power=nominal_power,
    #         allow_electricity_feed_in=allow_exports,
    #         # override template
    #         nominal_electrical_efficiency=nominal_electrical_efficiency,
    #         nominal_thermal_efficiency=nominal_thermal_efficiency,
    #         min_load_electrical_efficiency=min_load_electrical_efficiency,
    #         min_load_thermal_efficiency=min_load_thermal_efficiency,
    #         template=template
    #         )
    #     house_1.add(chp)

    #     # Add heat demands
    #     house_1.add(
    #         demands.FixedTemperatureHeating(
    #             name="heat_demand",
    #             min_flow_temperature=template.maximum_temperature,
    #             return_temperature=template.minimum_temperature,
    #             time_series=[
    #                 (nominal_power/template.nominal_electrical_efficiency)*
    #                 template.nominal_thermal_efficiency,
    #                 # the factor 0.99 is meant to force a demand below the min.
    #                 (nominal_power*template.normalised_min_load/
    #                   template.min_load_electrical_efficiency)*
    #                 template.min_load_thermal_efficiency*test_factor,
    #                 ],
    #         )
    #     )
        
    #     house_1.add(
    #         demands.Electricity(
    #             name="electricity_demand",
    #             time_series=[
    #                 nominal_power, 
    #                 nominal_power*template.normalised_min_load
    #                 ],
    #         )
    #     )

    #     solph_representation = SolphModel(
    #         energy_system,
    #         timeindex={
    #             "start": "2022-06-01 08:00:00",
    #             # "end": "2022-06-01 9:00:00",
    #             "end": "2022-06-01 10:00:00",
    #             "freq": "60T",
    #             "tz": "Europe/Berlin",
    #         },
    #     )

    #     solph_representation.build_solph_model()
    #     solved_model = solph_representation.solve(solve_kwargs={"tee": False})
    #     mr = meta_results(solved_model)
    #     assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)

# *****************************************************************************
# *****************************************************************************
