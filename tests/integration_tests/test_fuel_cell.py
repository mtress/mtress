from mtress.technologies import AFC, AEMFC, PEMFC, FuelCell, OffsetFuelCell
from mtress.technologies import SlackNode
from mtress.physics import HYDROGEN
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
from pyomo.opt import SolverFactory

solver = "scip" if SolverFactory("scip").available() else "cbc"


class TestFuelCell:

    def _check_fc_obj(self, fc, template, name="fc", nominal_power=100e3):
        assert fc.name == name
        assert fc.nominal_power == nominal_power
        assert (
            fc.full_load_electrical_efficiency
            == template.full_load_electrical_efficiency
        )
        assert (
            fc.full_load_thermal_efficiency
            == template.full_load_thermal_efficiency
        )
        assert fc.maximum_temperature == template.maximum_temperature
        assert fc.gas_input_pressure == template.gas_input_pressure

    @pytest.mark.parametrize(
        "template, expected_result",
        [(AFC, 0.342255559), (PEMFC, 0.314030005), (AEMFC, 0.3678928605)],
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
                temperature_levels=[20, template.maximum_temperature]
            )
        )

        # house_1.add(SlackNode({carriers.HeatCarrier: 1e9}))

        fc = FuelCell("fc", nominal_power=10e3, template=template)
        self._check_fc_obj(fc, template, nominal_power=fc.nominal_power)
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
                "freq": "60min",
                "tz": "Europe/Berlin",
            },
        )

        solph_representation.build_solph_model()
        solved_model = solph_representation.solve(
            solver=solver, solve_kwargs={"tee": False}
        )
        mr = Results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)


class TestOffsetFuelCell:

    def _check_fc_obj(self, fc, template, name="fc", nominal_power=100e3):
        assert fc.name == name
        assert fc.nominal_power == nominal_power
        assert (
            fc.full_load_electrical_efficiency
            == template.full_load_electrical_efficiency
        )
        assert (
            fc.full_load_thermal_efficiency
            == template.full_load_thermal_efficiency
        )
        assert (
            fc.min_load_electrical_efficiency
            == template.min_load_electrical_efficiency
        )
        assert (
            fc.min_load_thermal_efficiency
            == template.min_load_thermal_efficiency
        )
        assert fc.maximum_temperature == template.maximum_temperature
        assert fc.gas_input_pressure == template.gas_input_pressure

    @pytest.mark.parametrize(
        "template, minimum_load, expected_result, abs_tol",
        [
            (AFC, 0, 0.342255559, 1e-3),
            (PEMFC, 0, 0.314030005, 1e-3),
            (AEMFC, 0, 0.3678928605, 1e-3),
            (AFC, AFC.minimum_load, 38281175232.12961, 768),
            (PEMFC, PEMFC.minimum_load, 34453057708.92166, 292),
            (AEMFC, AEMFC.minimum_load, 49218653869.86667, 131),
        ],
    )
    def test_ofc(self, template, minimum_load, expected_result, abs_tol):

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
                    template.maximum_temperature,
                ],
            )
        )

        # house_1.add(SlackNode({carriers.HeatCarrier: 1e9}))

        fc = OffsetFuelCell(
            "fc",
            nominal_power=100e3,
            minimum_load=minimum_load,
            template=template,
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

        house_1.add(technologies.SlackNode())

        solph_representation = SolphModel(
            energy_system,
            timeindex={
                "start": "2022-06-01 08:00:00",
                "end": "2022-06-01 09:00:00",
                "freq": "60min",
                "tz": "Europe/Berlin",
            },
        )

        solph_representation.build_solph_model()
        solved_model = solph_representation.solve(
            solver=solver, solve_kwargs={"tee": False}
        )
        mr = Results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=abs_tol)

    @pytest.mark.parametrize(
        "nominal_power, template, elec_demand, expected_result",
        [
            # reference: nominal power matches demand
            (1000, PEMFC, 1000, 8.3341668e-05),
            # maximum power cannot be exceeded (imports are needed)
            (1000, PEMFC, 1500, 8.3341668e-05 + 500 * 50e-6),
            # minimum power has to be observed (=leads to penalties)
            (1000, PEMFC, 50, 50 * 50e-6),
        ],
    )
    def test_power_limits(
        self, nominal_power, template, elec_demand, expected_result
    ):

        os.chdir(os.path.dirname(__file__))
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
                    HYDROGEN: [template.gas_input_pressure],
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

        fc = OffsetFuelCell(
            name="fc",
            nominal_power=nominal_power,
            template=template,
        )
        house_1.add(fc)

        house_1.add(
            technologies.GasGridConnection(
                gas_type=HYDROGEN,
                grid_pressure=template.gas_input_pressure,
                working_rate=1e-3,
            )
        )

        # Add heat demands
        house_1.add(
            demands.FixedTemperatureHeating(
                name="heat_demand",
                min_flow_temperature=template.maximum_temperature,
                return_temperature=template.minimum_temperature,
                time_series=[500],
            )
        )

        house_1.add(
            demands.Electricity(
                name="electricity_demand",
                time_series=[elec_demand],
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
        assert math.isclose(expected_result, mr["objective"], abs_tol=1e-3)
