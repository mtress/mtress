import math
import pytest
import os
import pyomo.environ as pyo
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
    # OffsetCHP,
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
        assert chp.nominal_electrical_efficiency == template.nominal_electrical_efficiency
        assert chp.nominal_thermal_efficiency == template.nominal_thermal_efficiency
        # assert chp.min_load_electrical_efficiency ==
        # template.min_load_electrical_efficiency
        # assert chp.min_load_nominal_thermal_efficiency ==
        # template.min_load_nominal_thermal_efficiency
        # assert chp.full_load_electrical_efficiency ==
        # template.full_load_electrical_efficiency
        # assert chp.full_load_nominal_thermal_efficiency ==
        # template.full_load_nominal_thermal_efficiency
        # assert chp.min_load_electrical_efficiency ==
        # template.min_load_electrical_efficiency
        # assert chp.min_load_nominal_thermal_efficiency ==
        # template.min_load_nominal_thermal_efficiency
        assert chp.maximum_temperature == template.maximum_temperature
        assert chp.minimum_temperature == template.minimum_temperature
        assert chp.input_pressure == template.input_pressure
        assert chp.gas_type == template.gas_type
        assert type(chp.gas_type) is dict

    @pytest.mark.parametrize(
        "template, expected_result",
        [
            (NATURALGAS_CHP, 0.8508048112500001),
            (BIOGAS_CHP, 58187714401.612885),
            (BIOMETHANE_CHP, 0.7855700564999999),
            (HYDROGEN_CHP, 0.32534810449999996),
            (HYDROGEN_MIXED_CHP, 1307692350000.05),
            (AET100NG_CHP, 0.8077001939999999),
        ],
    )
    def test_chp(self, template: CHPTemplate, expected_result: float):

        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(technologies.ElectricityGridConnection(working_rate=50e-6))

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

        chp = CHP("chp", template=template)
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

        # TODO: make sure gas is being imported
        # TODO: make sure electricity is being produced
        # TODO: make sure electricity is not being imported
        # TODO: make sure heat is being produced


# class TestOffsetCHP:

#     def check_chp_template(self, chp: CHP, template: CHPTemplate):

#         assert chp.full_load_electrical_efficiency ==
# template.full_load_electrical_efficiency
#         assert chp.full_load_nominal_thermal_efficiency ==
#  template.full_load_nominal_thermal_efficiency
#         assert chp.min_load_electrical_efficiency ==
#  template.min_load_electrical_efficiency
#         assert chp.min_load_nominal_thermal_efficiency ==
# template.min_load_nominal_thermal_efficiency
#         assert chp.maximum_temperature == template.maximum_temperature
#         assert chp.minimum_temperature == template.minimum_temperature
#         assert chp.input_pressure == template.input_pressure
#         assert chp.gas_type == template.gas_type
#         assert type(chp.gas_type) is dict

#     @pytest.mark.parametrize(
#         "template, expected_result",
#         [(NATURALGAS_CHP, 1466.5878210550002),
#          (BIOGAS_CHP, 966.562821055),
#          (BIOMETHANE_CHP, 0.5883656500000001),
#          (HYDROGEN_CHP, 0.5883656500000001),
#          (HYDROGEN_MIXED_CHP,  0.557825485)],
#     )
#     def test_chp(self, template, expected_result):

#         os.chdir(os.path.dirname(__file__))
#         energy_system = MetaModel()
#         house_1 = Location(name="house_1")
#         energy_system.add_location(house_1)

#         house_1.add(carriers.ElectricityCarrier())
#      house_1.add(technologies.ElectricityGridConnection(working_rate=50e-6))

#         house_1.add(
#             carriers.GasCarrier(
#                 gases={
#                     HYDROGEN: [template.input_pressure],
#                 }
#             )
#         )

#         house_1.add(
#             carriers.HeatCarrier(
#                 temperature_levels=[20, template.maximum_temperature],
#                 reference_temperature=10,
#             )
#         )

#         fc = CHP("chp", nominal_power=10e3, template=template)
#         self.check_chp_template(fc, template)
#         house_1.add(fc)

#         house_1.add(
#             technologies.GasGridConnection(
#                 gas_type=HYDROGEN,
#                 grid_pressure=template.input_pressure,
#                 working_rate=5,
#             )
#         )

#         # Add heat demands
#         house_1.add(
#             demands.FixedTemperatureHeating(
#                 name="heat_demand",
#                 min_flow_temperature=template.maximum_temperature,
#                 return_temperature=template.minimum_temperature,
#                 time_series=[1000],
#             )
#         )

#         house_1.add(
#             demands.Electricity(
#                 name="electricity_demand",
#                 time_series=[1000],
#             )
#         )

#         solph_representation = SolphModel(
#             energy_system,
#             timeindex={
#                 "start": "2022-06-01 08:00:00",
#                 "end": "2022-06-01 09:00:00",
#                 "freq": "60T",
#                 "tz": "Europe/Berlin",
#             },
#         )

#         solph_representation.build_solph_model()
#       solved_model = solph_representation.solve(solve_kwargs={"tee": False})
#         mr = meta_results(solved_model)
#         assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)
