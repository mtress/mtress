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

    def test_fc_template_aem(self):

        # Considering AEMFC template type
        fc = FuelCell(
            name="fc-aem", 
            nominal_power=100e3, 
            template=AEMFC
            )

        assert fc.name == "fc-aem"
        assert fc.nominal_power == 100e3
        assert fc.full_load_electrical_efficiency == AEMFC.full_load_electrical_efficiency
        assert fc.full_load_thermal_efficiency == AEMFC.full_load_thermal_efficiency
        assert fc.maximum_temperature == AEMFC.maximum_temperature
        assert fc.gas_input_pressure == AEMFC.gas_input_pressure
        # assert fc.gas_type == AEMFC.gas_type
        # assert type(AEMFC.gas_type) is dict

    def test_fc_template_pem(self):

        # Considering PEMFC template type
        fc = FuelCell(
            name="fc-pem", 
            nominal_power=100e3, 
            template=PEMFC
            )

        assert fc.name == "fc-pem"
        assert fc.nominal_power == 100e3
        assert fc.full_load_electrical_efficiency == PEMFC.full_load_electrical_efficiency
        assert fc.full_load_thermal_efficiency == PEMFC.full_load_thermal_efficiency
        assert fc.maximum_temperature == PEMFC.maximum_temperature
        assert fc.gas_input_pressure == PEMFC.gas_input_pressure
        # assert fc.gas_type == PEMFC.gas_type
        # assert type(fc.gas_type) is dict

    def test_fc_template_afc(self):

        # Considering PEMFC template type
        fc = FuelCell(
            name="fc-afc", 
            nominal_power=100e3, 
            template=AFC
            )

        assert fc.name == "fc-afc"
        assert fc.nominal_power == 100e3
        assert fc.full_load_electrical_efficiency == AFC.full_load_electrical_efficiency
        assert fc.full_load_thermal_efficiency == AFC.full_load_thermal_efficiency
        assert fc.maximum_temperature == AFC.maximum_temperature
        assert fc.gas_input_pressure == AFC.gas_input_pressure
        # assert fc.gas_type == AFC.gas_type
        # assert type(fc.gas_type) is dict

    def test_fc(self):

        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(technologies.ElectricityGridConnection(working_rate=50e-6))

        house_1.add(
            carriers.GasCarrier(
                gases={
                    HYDROGEN: [AEMFC.gas_input_pressure],
                }
            )
        )

        house_1.add(
            carriers.HeatCarrier(
                temperature_levels=[20, 55],
                reference_temperature=10,
            )
        )

        house_1.add(
            FuelCell(
                "fc-aem", 
                nominal_power=10e3,
                template=AEMFC
                )
        )

        house_1.add(
            technologies.GasGridConnection(
                gas_type=HYDROGEN,
                grid_pressure=AEMFC.gas_input_pressure,
                working_rate=5,
            )
        )

        # Add heat demands
        house_1.add(
            demands.FixedTemperatureHeating(
                name="heat_demand",
                min_flow_temperature=55,
                return_temperature=20,
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
        pyomo_objective = 0.3678928605
        assert math.isclose(pyomo_objective, mr["objective"], abs_tol=3e-3)
        
class TestOffsetFuelCell:

    def test_ofc_template_aem(self):

        # Considering AEMFC template type
        fc = OffsetFuelCell(
            name="fc-aem", 
            nominal_power=100e3, 
            template=AEMFC
            )

        assert fc.name == "fc-aem"
        assert fc.nominal_power == 100e3
        assert fc.full_load_electrical_efficiency == AEMFC.full_load_electrical_efficiency
        assert fc.full_load_thermal_efficiency == AEMFC.full_load_thermal_efficiency
        assert fc.min_load_electrical_efficiency == AEMFC.min_load_electrical_efficiency
        assert fc.min_load_thermal_efficiency == AEMFC.min_load_thermal_efficiency
        assert fc.maximum_temperature == AEMFC.maximum_temperature
        assert fc.gas_input_pressure == AEMFC.gas_input_pressure
        # assert fc.gas_type == AEMFC.gas_type
        # assert type(AEMFC.gas_type) is dict

    def test_ofc_template_pem(self):

        # Considering PEMFC template type
        fc = OffsetFuelCell(
            name="fc-pem", 
            nominal_power=100e3, 
            template=PEMFC
            )

        assert fc.name == "fc-pem"
        assert fc.nominal_power == 100e3
        assert fc.full_load_electrical_efficiency == PEMFC.full_load_electrical_efficiency
        assert fc.full_load_thermal_efficiency == PEMFC.full_load_thermal_efficiency
        assert fc.min_load_electrical_efficiency == PEMFC.min_load_electrical_efficiency
        assert fc.min_load_thermal_efficiency == PEMFC.min_load_thermal_efficiency
        assert fc.maximum_temperature == PEMFC.maximum_temperature
        assert fc.gas_input_pressure == PEMFC.gas_input_pressure
        # assert fc.gas_type == PEMFC.gas_type
        # assert type(fc.gas_type) is dict

    def test_ofc_template_afc(self):

        # Considering PEMFC template type
        fc = OffsetFuelCell(
            name="fc-afc", 
            nominal_power=100e3, 
            template=AFC
            )

        assert fc.name == "fc-afc"
        assert fc.nominal_power == 100e3
        assert fc.full_load_electrical_efficiency == AFC.full_load_electrical_efficiency
        assert fc.full_load_thermal_efficiency == AFC.full_load_thermal_efficiency
        assert fc.min_load_electrical_efficiency == AFC.min_load_electrical_efficiency
        assert fc.min_load_thermal_efficiency == AFC.min_load_thermal_efficiency
        assert fc.maximum_temperature == AFC.maximum_temperature
        assert fc.gas_input_pressure == AFC.gas_input_pressure
        # assert fc.gas_type == AFC.gas_type
        # assert type(fc.gas_type) is dict

    @pytest.mark.parametrize(
        "norm_min_power, expected_result", 
        [(0, 0.3678928605),
         (0.5, 1571428590000.05)]
        )
    def test_ofc(self, norm_min_power, expected_result):

        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(technologies.ElectricityGridConnection(working_rate=50e-6))

        house_1.add(
            carriers.GasCarrier(
                gases={
                    HYDROGEN: [AEMFC.gas_input_pressure],
                }
            )
        )

        house_1.add(
            carriers.HeatCarrier(
                temperature_levels=[20, 55],
                reference_temperature=10,
            )
        )

        house_1.add(
            OffsetFuelCell(
                "fc-aem", 
                nominal_power=10e3,
                minimum_load=norm_min_power,
                template=AEMFC
                )
        )

        house_1.add(
            technologies.GasGridConnection(
                gas_type=HYDROGEN,
                grid_pressure=AEMFC.gas_input_pressure,
                working_rate=5,
            )
        )

        # Add heat demands
        house_1.add(
            demands.FixedTemperatureHeating(
                name="heat_demand",
                min_flow_temperature=55,
                return_temperature=20,
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
