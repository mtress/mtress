from mtress.technologies import (
    ElectricVehicle, 
    GenericElectricVehicle,
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
from pandas import Series

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
            plugged_in_profile=[
                1 if static_discharge > 0 else 0,
                1 if static_discharge > 0 else 0,
                1 if static_discharge > 0 else 0,
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
        
    @pytest.mark.parametrize(
        "template, status, expected_result",
        [# reference result for GenericSegmentB_EV
         (GenericSegmentB_EV, [1, 1, 1], 181258.97368415), 
         # not being connected worsens results
         (GenericSegmentB_EV,  [1, 0, 1], 186008.92105265), 
         # reference result for GenericSegmentC_EV
         (GenericSegmentC_EV,  [1, 1, 1], 157509.23684205), 
         # not being connected worsens results
         (GenericSegmentC_EV,  [1, 0, 1], 162259.18421055)],
    )    
    def test_ev_status(self, template, status, expected_result):

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
        static_discharge = 1e3
        ev = ElectricVehicle(
            name="ev", 
            fixed_losses_absolute=[
                static_discharge,
                static_discharge,
                static_discharge
                ],
            plugged_in_profile=status,
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
        
    @pytest.mark.parametrize(
        "plugged_in_profile, static_discharge_profile",
        [
         # error: plugged-in and with static discharge
         # 1) int and int
         (1, 1), 
         # 2) int and list
         (1, [0, 0, 1000]),
         (1, [1000, 1000, 1000]), 
         # 3) int and Series
         (1, Series(data=[0, 0, 1000])),
         (1, Series(data=[1000, 1000, 1000])),
         # 4) list and int
         ([1], 1), 
         # 5) list and list
         ([1, 1, 1], [1000, 1000, 1000]), 
         ([0, 0, 1], [0, 1000, 1000]), 
         # 6) list and Series
         ([1, 1, 1], Series(data=[1000, 1000, 1000])), 
         ([0, 0, 1], Series(data=[0, 1000, 1000])), 
         # 7) Series and int
         (Series(data=[1, 1, 1]), 1), 
         (Series(data=[0, 0, 1]), 1), 
         # 8) Series and list
         (Series(data=[1, 1, 1]), [1000, 1000, 1000]), 
         (Series(data=[0, 0, 1]), [0, 1000, 1000]), 
         # 9) Series and Series
         (Series(data=[1, 1, 1]), Series(data=[0, 0, 1000])), 
         (Series(data=[0, 0, 1]), Series(data=[1000, 1000, 1000])),
         
         # error: sizes do not match
         # 5) list and list
         ([1, 1, 1, 1], [1000, 1000, 1000]), 
         ([0, 0, 1, 1], [0, 1000, 1000]), 
         # 6) list and Series
         ([1, 1, 1, 1], Series(data=[1000, 1000, 1000])), 
         ([0, 0, 1, 1], Series(data=[0, 1000, 1000])), 
         # 8) Series and list
         (Series(data=[1, 1, 1, 1]), [1000, 1000, 1000]), 
         (Series(data=[0, 0, 1, 1]), [0, 1000, 1000]), 
         # 9) Series and Series
         (Series(data=[1, 1, 1, 1]), Series(data=[0, 0, 1000])), 
         (Series(data=[0, 0, 1, 1]), Series(data=[1000, 1000, 1000])),
         
         # error: discharge rates exceed the maximum discharge rate
         # max rate: template.nominal_capacity*template.discharging_C_Rate
         # int, int
         (0, 1+52e3*50 / 52), 
         # int, list
         (0, [0, 1+52e3*50 / 52]), 
         # int, Series
         (0, Series(data=[0, 1+52e3*50 / 52])), 
         # list, int,
         ([0, 0], 1+52e3*50 / 52), 
         # list, list
         ([0, 0], [0, 1+52e3*50 / 52]), 
         # list, Series
         ([0, 0], Series(data=[0, 1+52e3*50 / 52])), 
         # Series, int
         (Series(data=[0, 0]), 1+52e3*50 / 52), 
         # Series, list
         (Series(data=[0, 0]), [0, 1+52e3*50 / 52]), 
         # Series, Series
         (Series(data=[0, 0]), Series(data=[0, 1+52e3*50 / 52])), 
         ],
    )    
    def test_trigger_profile_errors(
            self, 
            plugged_in_profile,
            static_discharge_profile
            ):

        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(
            technologies.ElectricityGridConnection(
                working_rate=50e-6
                )
            )
        
        with pytest.raises(ValueError):
            GenericElectricVehicle(
                name="ev", 
                static_discharge_profile=static_discharge_profile,
                plugged_in_profile=plugged_in_profile,
                nominal_capacity=52e3,  # 52 kWh
                charging_C_Rate=50 / 52,  # 50 kW
                discharging_C_Rate=50 / 52,  # 50 kW
                charging_efficiency=0.95,
                discharging_efficiency=0.95, 
                loss_rate=0
                )
            # ElectricVehicle(consumption_per_distance, kwargs)
            
# *****************************************************************************
# *****************************************************************************