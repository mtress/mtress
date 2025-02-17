from mtress.technologies import BatteryStorage, PowerWallGenI, PowerWallGenII
from mtress.technologies._battery_storage import BatteryStorageTemplate
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
    technologies,
)


class TestBatteryStorage:

    def _check_bs_obj(
        self, bs: BatteryStorage, template: BatteryStorageTemplate, name="bs"
    ):
        assert bs.name == name
        assert bs.charging_C_Rate == template.charging_C_Rate
        assert bs.discharging_C_Rate == template.discharging_C_Rate
        assert bs.charging_efficiency == template.charging_efficiency
        assert bs.discharging_efficiency == template.discharging_efficiency
        assert bs.loss_rate == template.loss_rate
        assert bs.nominal_capacity == template.nominal_capacity

    @pytest.mark.parametrize(
        "template, renewable_generation, expected_result",
        [
            (PowerWallGenI, False, 1466.5878210550002),
            (PowerWallGenI, True, 966.562821055),
            (PowerWallGenII, False, 0.5883656500000001),
            (PowerWallGenII, True, 0.557825485),
        ],
    )
    def test_bs(self, template, renewable_generation, expected_result):

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

        bs = BatteryStorage(name="bs", template=template)
        self._check_bs_obj(bs, template)
        house_1.add(bs)

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
                    specific_generation=[1, 0, 0.2],
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
        assert bs.fixed_losses_absolute == 0.0
