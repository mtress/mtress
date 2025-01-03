from mtress.technologies import AFC, AEMFC, PEMFC, FuelCell, OffsetFuelCell
from mtress.physics import HYDROGEN
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

class TestFuelCell:

    def _check_fc_obj(self, fc, template, name="fc", nominal_power=100e3):
        assert fc.name == name
        assert fc.nominal_power == nominal_power
        assert fc.full_load_electrical_efficiency == template.full_load_electrical_efficiency
        assert fc.full_load_thermal_efficiency == template.full_load_thermal_efficiency
        assert fc.maximum_temperature == template.maximum_temperature
        assert fc.gas_input_pressure == template.gas_input_pressure

    @pytest.mark.parametrize(
         "template, expected_result", 
         [(AFC, 0.342255559),
          (PEMFC, 0.314030005),
          (AEMFC, 0.3678928605)]
         )
    def test_fc(self, template, expected_result):

        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(technologies.ElectricityGridConnection(working_rate=50e-6))

        house_1.add(
            carriers.GasCarrier(
                gases={
                    HYDROGEN: [template.gas_input_pressure],
                }
            )
        )

        house_1.add(
            carriers.HeatCarrier(
                temperature_levels=[20, template.maximum_temperature],
                reference_temperature=10,
            )
        )

        fc = FuelCell(
            "fc", 
            nominal_power=10e3,
            template=template
            )
        house_1.add(fc)

        house_1.add(
            technologies.GasGridConnection(
                gas_type=HYDROGEN,
                grid_pressure=template.gas_input_pressure,
                working_rate=5,
            )
        )

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
        
class TestOffsetFuelCell:
    
    def _check_fc_obj(self, fc, template, name="fc", nominal_power=100e3):
        assert fc.name == name
        assert fc.nominal_power == nominal_power
        assert fc.full_load_electrical_efficiency == template.full_load_electrical_efficiency
        assert fc.full_load_thermal_efficiency == template.full_load_thermal_efficiency
        assert fc.min_load_electrical_efficiency == template.min_load_electrical_efficiency
        assert fc.min_load_thermal_efficiency == template.min_load_thermal_efficiency
        assert fc.maximum_temperature == template.maximum_temperature
        assert fc.gas_input_pressure == template.gas_input_pressure

    @pytest.mark.parametrize(
        "template, norm_min_power, expected_result",
        [(AFC, 0, 0.342255559),
         (PEMFC, 0, 0.314030005),
         (AEMFC, 0, 0.3678928605),
         (AFC, AFC.minimum_load, 1444444420000.05),
         (PEMFC, PEMFC.minimum_load, 1400000000000.05),
         (AEMFC, AEMFC.minimum_load, 1571428590000.05)]
        )
    def test_ofc(self, template, norm_min_power, expected_result):

        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(technologies.ElectricityGridConnection(working_rate=50e-6))

        house_1.add(
            carriers.GasCarrier(
                gases={
                    HYDROGEN: [template.gas_input_pressure],
                }
            )
        )

        house_1.add(
            carriers.HeatCarrier(
                temperature_levels=[
                    template.minimum_temperature, 
                    template.maximum_temperature
                    ],
                reference_temperature=10,
            )
        )
        
        fc = OffsetFuelCell(
            "fc", 
            nominal_power=100e3,
            minimum_load=norm_min_power,
            template=template
            )
        self._check_fc_obj(fc, template)
        house_1.add(fc)

        house_1.add(
            technologies.GasGridConnection(
                gas_type=HYDROGEN,
                grid_pressure=template.gas_input_pressure,
                working_rate=5,
            )
        )

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
