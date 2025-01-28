from mtress.technologies import ElectricVehicle, EV1, EV2
from mtress.technologies._ev import ElectricVehicleTemplate
from mtress.technologies import RenewableElectricitySource
# from mtress.physics import HYDROGEN
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

    @pytest.mark.parametrize(
        "template, renewable_generation, expected_result",
        [(EV1, False, 1466.5878210550002), 
         (EV1, True, 966.562821055), 
         (EV2, False, 0.5883656500000001), 
         (EV2, True, 0.557825485)],
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

        house_1.add(
            demands.Electricity(
                name="electricity_demand",
                time_series=[3000, 5000, 3400],
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
