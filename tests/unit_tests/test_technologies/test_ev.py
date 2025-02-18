from mtress.technologies import (
    ElectricVehicle, 
    GenericSegmentB_EV, 
    GenericSegmentC_EV
    )
from mtress.technologies._ev import ElectricVehicleTemplate
from mtress.technologies import RenewableElectricitySource
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
    technologies
)


class TestElectricVehicle:

    def check_ev_obj(
            self, 
            bs: ElectricVehicle, 
            template: ElectricVehicleTemplate, 
            nominal_capacity=None,
            name="ev"
            ):
        assert bs.name == name
        assert (
            bs.nominal_capacity == template.nominal_capacity
            if nominal_capacity is None else 
            bs.nominal_capacity == nominal_capacity 
            )
        assert bs.charging_C_Rate == template.charging_C_Rate
        assert bs.discharging_C_Rate == template.discharging_C_Rate
        assert bs.charging_efficiency == template.charging_efficiency
        assert bs.discharging_efficiency == template.discharging_efficiency
        assert bs.loss_rate == template.loss_rate
        assert bs.consumption_per_distance == template.consumption_per_distance
        assert bs.fixed_losses_absolute == 0.0
        
    # TODO: test availability
    # TODO: test fixed profile

    @pytest.mark.parametrize(
        "template, renewable_generation, expected_result",
        [(GenericSegmentB_EV, False, 176508.86842105), 
         (GenericSegmentB_EV, True, 176008.84342105), 
         (GenericSegmentC_EV, False, 152759.13157895), 
         (GenericSegmentC_EV, True, 152259.10657895)],
    )
    def test_ev(self, template, renewable_generation, expected_result):

        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(
            technologies.ElectricityGridConnection(
                working_rate=[50e-6, 50e-6, 5]
                )
            )
        
        ev = ElectricVehicle(name="ev", template=template)
        self.check_ev_obj(ev, template)
        house_1.add(ev)
        # ev1 = ElectricVehicle(n)
        house_1.add(
            demands.Electricity(
                name="electricity_demand",
                time_series=[30000, 120000, 60000],
            )
        )
        
        # supply
        if renewable_generation:
            house_1.add(
                RenewableElectricitySource(
                    name="renewable_electricity", 
                    nominal_power=500, 
                    specific_generation=[1, 0, 0.2]
                    )
                )
        
        solph_representation = SolphModel(
            energy_system,
            timeindex={
                "start": "2022-06-01 08:00:00",
                "end": "2022-06-01 11:00:00",
                "freq": "60T",
                "tz": "Europe/Berlin",
            },
        )

        solph_representation.build_solph_model()
        solved_model = solph_representation.solve(solve_kwargs={"tee": False})
        mr = meta_results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)
        
        

    @pytest.mark.parametrize(
        "template, static_discharge, expected_result",
        [(GenericSegmentB_EV, 1e3, 181258.97368415), 
         (GenericSegmentB_EV, 1e4, 224009.92105285), 
         (GenericSegmentC_EV, 1e3, 157509.23684205), 
         (GenericSegmentC_EV, 1e4, 200260.18421075)],
    )
    def test_ev_profile(self, template, static_discharge, expected_result):

        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(
            technologies.ElectricityGridConnection(
                working_rate=[50e-6, 50e-6, 5]
                )
            )
        
        ev = ElectricVehicle(
            name="ev", 
            fixed_losses_absolute=[
                static_discharge,
                static_discharge,
                static_discharge
                ],
            template=template
            )
        house_1.add(ev)
        house_1.add(
            demands.Electricity(
                name="electricity_demand",
                time_series=[30000, 120000, 60000],
            )
        )
        
        solph_representation = SolphModel(
            energy_system,
            timeindex={
                "start": "2022-06-01 08:00:00",
                "end": "2022-06-01 11:00:00",
                "freq": "60T",
                "tz": "Europe/Berlin",
            },
        )

        solph_representation.build_solph_model()
        solved_model = solph_representation.solve(solve_kwargs={"tee": False})
        mr = meta_results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)
