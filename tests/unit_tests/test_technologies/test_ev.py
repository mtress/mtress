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
        
    
    @staticmethod
    def result(
            template: ElectricVehicleTemplate,
            initial_soc=0.5,
            soc_max=1,
            prices=[50e-6,5],
            loads=[150e3, 60e3],
            renewables=[0, 0],
            losses=[0, 0],
            ):
        
        return (
            prices[0]*(
                loads[0]+
                (template.nominal_capacity*(
                    soc_max-initial_soc
                    )+losses[0])/(
                    template.charging_efficiency
                    )
                -renewables[0]
            )+prices[1]*(
                loads[1]
                -(template.nominal_capacity*(
                    soc_max-initial_soc
                    )-losses[1])*template.discharging_efficiency
                -renewables[1]
                )
            )
    
    @pytest.mark.parametrize(
        "template, renewable_generation, expected_result",
        [
         # results can be obtained with the result method
         (GenericSegmentB_EV, False, 176508.868421),
         (GenericSegmentB_EV, True, 176008.843421), 
         (GenericSegmentC_EV, False, 152759.1145835), 
         (GenericSegmentC_EV, True, 152259.0895835)
         ],
    )
    def test_ev(self, template, renewable_generation, expected_result):
        "Test a simple problem with stationary EV without losses."
        
        # what happens?
        # 1) the storage is charged to the max to be discharged during the last
        # time interval, since that has the highest electricity prices
        # 2) the charge level at the last time interval has to be the same as
        # during the first time interval, which determines how much can/has to 
        # be discharged during the last time interval
        # 3) if the C rates are above the threshold needed to satisfy the load
        # during the last time interval and the respective charging above the 
        # initial level, and no losses exist, then the charging and discharging
        # of the battery can take place in separate but single steps
        
        prices = [50e-6, 5]
        loads = [150000, 60000]
        renewables = [500, 100]
        time_index = {
            "start": "2022-06-01 08:00:00",
            "end": "2022-06-01 10:00:00",
            "freq": "60T",
            "tz": "Europe/Berlin",
        }

        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(
            technologies.ElectricityGridConnection(
                working_rate=prices
                )
            )
        
        ev = ElectricVehicle(name="ev", template=template)
        self.check_ev_obj(ev, template)
        house_1.add(ev)
        house_1.add(
            demands.Electricity(
                name="electricity_demand",
                time_series=loads,
            )
        )
        
        # supply
        if renewable_generation:
            house_1.add(
                RenewableElectricitySource(
                    name="renewable_electricity", 
                    nominal_power=max(renewables), 
                    specific_generation=[
                        ren/max(renewables)
                        for ren in renewables
                        ]
                    )
                )
        
        solph_representation = SolphModel(
            energy_system,
            timeindex=time_index,
        )

        solph_representation.build_solph_model()
        solved_model = solph_representation.solve(solve_kwargs={"tee": False})
        mr = meta_results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=1e-3)
        assert math.isclose(
            mr["objective"],
            self.result(
                template,
                renewables=renewables if renewable_generation else [0, 0]
                ), 
            abs_tol=1e-3
            )
        
    # *************************************************************************
    # *************************************************************************
    
    @pytest.mark.parametrize(
        "template, fixed_losses, _type, expected_result",
        [
         # float
         (GenericSegmentB_EV, 1e3, float, 181258.9210525), 
         (GenericSegmentB_EV, 1e4, float, 224009.394737), 
         (GenericSegmentC_EV, 1e3, float, 157509.1666665), 
         (GenericSegmentC_EV, 1e4, float, 200259.6354165),
         # list
         (GenericSegmentB_EV, 1e3, list, 181258.9210525), 
         (GenericSegmentB_EV, 1e4, list, 224009.394737), 
         (GenericSegmentC_EV, 1e3, list, 157509.1666665), 
         (GenericSegmentC_EV, 1e4, list, 200259.6354165),
         # Series
         (GenericSegmentB_EV, 1e3, Series, 181258.9210525), 
         (GenericSegmentB_EV, 1e4, Series, 224009.394737), 
         (GenericSegmentC_EV, 1e3, Series, 157509.1666665), 
         (GenericSegmentC_EV, 1e4, Series, 200259.6354165),
         ],
    )
    def test_ev_std_loss(self, template, fixed_losses, _type, expected_result):
        "Test a simple problem with stationary EV with losses."
        
        # what happens?
        # 1) the storage is charged to the max to be discharged during the last
        # time interval, since that has the highest electricity prices
        # 2) the charge level at the last time interval has to be the same as
        # during the first time interval, which determines how much can/has to 
        # be discharged during the last time interval
        # 3) if the C rates are above the threshold needed to satisfy the load
        # during the last time interval and the respective charging above the 
        # initial level, and no losses exist, then the charging and discharging
        # of the battery can take place in separate but single steps
        # 4) constant internal losses require additional charging in the first
        # time step and then a reduced discharge during the last time step,
        # which translate into a lower impact
        
        prices = [50e-6, 5]
        loads = [150000, 60000]
        time_index = {
            "start": "2022-06-01 08:00:00",
            "end": "2022-06-01 10:00:00",
            "freq": "60T",
            "tz": "Europe/Berlin",
        }
        
        # pick format
        if _type == list:
            _losses = [fixed_losses, fixed_losses]
            _fix_losses = _losses
        elif _type == Series:
            _losses = [fixed_losses, fixed_losses]
            _fix_losses = Series(
                data=_losses
                )
        else: # float
            _losses = [fixed_losses, fixed_losses]
            _fix_losses = fixed_losses
        
        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(
            technologies.ElectricityGridConnection(
                working_rate=prices
                )
            )
        
        ev = GenericElectricVehicle(
            name="ev", 
            fixed_losses_absolute=_fix_losses,
            template=template
            )
        house_1.add(ev)
        house_1.add(
            demands.Electricity(
                name="electricity_demand",
                time_series=loads,
            )
        )
        
        solph_representation = SolphModel(
            energy_system,
            timeindex=time_index,
        )
        # result: 
        solph_representation.build_solph_model()
        # solph_representation.model.write('thatproblem.lp')
        solved_model = solph_representation.solve(solve_kwargs={"tee": False})
        mr = meta_results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=1e-3)
        assert math.isclose(
            mr["objective"],
            self.result(
                template,
                losses=_losses
                ), 
            abs_tol=1e-3
            )
        
    # *************************************************************************
    # *************************************************************************
       
    @staticmethod
    def other_result(
            template: ElectricVehicleTemplate,
            initial_soc=0.5,
            soc_max=1,
            prices=[50e-6,50e-6,5],
            loads=[0, 150e3, 60e3],
            renewables=[0, 0, 0],
            losses=[0, 0, 0],
            discharge=0
            ):
        
        return (
            prices[0]*(
                loads[0]+
                (template.nominal_capacity*(
                    soc_max-initial_soc
                    )+losses[0])/(
                    template.charging_efficiency
                    )
                -renewables[0]
            )+
            prices[1]*(
                loads[1]
            )+
            prices[2]*(
                loads[2]
                -(template.nominal_capacity*(
                    soc_max-initial_soc
                    )-losses[2]
                    -discharge/template.discharging_efficiency
                    )*template.discharging_efficiency
                -renewables[2]
                )
            )
    
    @pytest.mark.parametrize(
        "template, discharge, _type, expected_result",
        [
         # list
         (GenericSegmentB_EV, 1e3, list, 181508.86842105), 
         (GenericSegmentB_EV, 1e4, list, 226508.86842105), 
         (GenericSegmentC_EV, 1e3, list, 157759.11458335), 
         (GenericSegmentC_EV, 1e4, list, 202759.11458335),
         # Series
         (GenericSegmentB_EV, 1e3, Series, 181508.86842105), 
         (GenericSegmentB_EV, 1e4, Series, 226508.86842105), 
         (GenericSegmentC_EV, 1e3, Series, 157759.11458335), 
         (GenericSegmentC_EV, 1e4, Series, 202759.11458335),
         ],
    )
    def test_ev_profile(self, template, discharge, _type, expected_result):
        "Test a problem with non-stationary EV."
        # tests the static demand profile
        
        # pick format
        if _type == list:
            _discharge_profile = [
                0,
                discharge, 
                0
                ]
            _connected_status_profile = [
                1,
                0 if discharge > 0 else 1,
                1
                ]
        elif _type == Series:
            _discharge_profile = Series(
                data=[
                    0,
                    discharge, 
                    0
                    ]
                )
            _connected_status_profile = Series(data=[
                1,
                0 if discharge > 0 else 1,
                1
                ])
        
        prices = [50e-6, 50e-6, 5]
        loads = [0, 150000, 60000]
        time_index = {
            "start": "2022-06-01 08:00:00",
            "end": "2022-06-01 11:00:00",
            "freq": "60T",
            "tz": "Europe/Berlin",
        }

        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(
            technologies.ElectricityGridConnection(
                working_rate=prices
                )
            )
        
        ev = GenericElectricVehicle(
            name="ev", 
            static_discharge_profile=_discharge_profile,
            plugged_in_profile=_connected_status_profile,
            template=template
            )
        house_1.add(ev)
        house_1.add(
            demands.Electricity(
                name="electricity_demand",
                time_series=loads,
            )
        )
        
        solph_representation = SolphModel(
            energy_system,
            timeindex=time_index,
        )

        solph_representation.build_solph_model()
        # print(solph_representation.model.pprint())
        # solph_representation.model.write('thatproblem.lp')
        solved_model = solph_representation.solve(solve_kwargs={"tee": False})
        mr = meta_results(solved_model)
        # print(mr["objective"])
        assert math.isclose(expected_result, mr["objective"], abs_tol=1e-3)
        assert math.isclose(
            mr["objective"],
            self.other_result(
                template,
                discharge=discharge
                ), 
            abs_tol=1e-3
            )
    
    # *************************************************************************
    # *************************************************************************
    