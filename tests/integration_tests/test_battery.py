from mtress.technologies import (
    BatteryStorage,
    GenericBatteryModelI,
    GenericBatteryModelII,
)
from mtress.technologies._battery_storage import BatteryStorageTemplate
from mtress.technologies import RenewableElectricitySource
from pandas import Series


# from mtress.physics import HYDROGEN
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
        assert bs.fixed_losses_absolute == 0.0

    @pytest.mark.parametrize(
        "template, renewable_generation, expected_result",
        [
            (GenericBatteryModelI, False, 1466.5878210550002),
            (GenericBatteryModelI, True, 966.562821055),
            (GenericBatteryModelII, False, 0.5883656500000001),
            (GenericBatteryModelII, True, 0.557825485),
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

    @pytest.mark.parametrize(
        "template, fixed_load, _type, expected_result",
        [
            # worse than 1466.58...
            (GenericBatteryModelI, 1e2, float, 1952.03524737),
            (GenericBatteryModelI, 1e3, float, 6321.06218421),  # worser
            # worse than 0.588365...
            (GenericBatteryModelII, 1e2, float, 0.604155125),
            (GenericBatteryModelII, 1e3, float, 0.74626039),  # worser
            # list
            # worse than 1466.58...
            (GenericBatteryModelI, 1e2, list, 1952.03524737),
            (GenericBatteryModelI, 1e3, list, 6321.06218421),  # worser
            # worse than 0.588365...
            (GenericBatteryModelII, 1e2, list, 0.604155125),
            (GenericBatteryModelII, 1e3, list, 0.74626039),  # worser
            # Series
            # worse than 1466.58...
            (GenericBatteryModelI, 1e2, Series, 1952.03524737),
            (GenericBatteryModelI, 1e3, Series, 6321.06218421),  # worser
            # worse than 0.588365...
            (GenericBatteryModelII, 1e2, Series, 0.604155125),
            (GenericBatteryModelII, 1e3, Series, 0.74626039),  # worser
        ],
    )
    def test_bs_losses(self, template, fixed_load, _type, expected_result):
        # tests using a battery with losses

        # pick format
        if _type == list:
            _fix_losses = [fixed_load, fixed_load, fixed_load]
        elif _type == Series:
            _fix_losses = Series(data=[fixed_load, fixed_load, fixed_load])
        else:  # float
            _fix_losses = fixed_load

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

        bs = BatteryStorage(
            name="bs", fixed_losses_absolute=_fix_losses, template=template
        )
        house_1.add(bs)

        house_1.add(
            demands.Electricity(
                name="electricity_demand",
                time_series=[3000, 5000, 3400],
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
        solved_model = solph_representation.solve(
            solver=solver, solve_kwargs={"tee": False}
        )
        mr = Results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=3e-3)

    @pytest.mark.parametrize(
        "surplus, shared_limit, mutex, "
        + "expected_result, true_charging, true_discharging",
        [
            # no mutex
            # no shared limit
            # case 1: surplus of 0.1 leads to charging and discharging
            (0.1, False, False, 0, [1.349275, 0.1, 0], [1.349275, 0, 0]),
            # case 2: surplus leading to peak charging and discharging
            (
                0.22234156820622974,
                False,
                False,
                0,
                [3.0, 0.222342, 0],
                [3.0, 0, 0],
            ),
            # case 3: simultaneous charging and discharging in multiple steps
            (0.3, False, False, 0, [3.0, 1.347826, 0], [3.0, 1.047826, 0]),
            # case 1 with shared limit (no difference: limits not reached)
            (0.1, True, False, 0, [1.349275, 0.1, 0], [1.349275, 0, 0]),
            # case 2 with shared limit (chg and dchg amplitudes are limited)
            (
                0.22234156820622974,
                True,
                False,
                0,
                [1.5, 1.611171, 0.111171],
                [1.5, 1.388829, 0.111171],
            ),
            # case 3 with shared limit (chg and dchg amplitudes are limited)
            (
                0.3,
                True,
                False,
                0,
                [1.5, 1.65, 1.197826],
                [1.5, 1.35, 1.197826],
            ),
            # mutex
            # case 1: surplus of 0.1 leads to charging and discharging
            (0.1, False, True, None, [1.349275, 0.1, 0], [1.349275, 0, 0]),
            # case 2: surplus leading to peak charging and discharging
            (
                0.22234156820622974,
                False,
                True,
                None,
                [3.0, 0.222342, 0],
                [3.0, 0, 0],
            ),
            # case 3: simultaneous charging and discharging in multiple steps
            (0.3, False, True, None, [3.0, 1.347826, 0], [3.0, 1.047826, 0]),
        ],
    )
    def test_bs_limit(
        self,
        surplus,
        shared_limit,
        mutex,
        expected_result,
        true_charging,
        true_discharging,
    ):

        if mutex and solver == "cbc":
            # skip tests involving mutex if cbc is to be used (no sos support)
            return

        # tests
        # - to force the battery to charge and discharge at the same time
        # - to force charging and discharging to be mutually exclusive

        # a surplus of X will require the battery to waste it by charging and
        # discharging, since there is no other feasible option (no exports nor
        # curtailment). This surplus creates a SOC increase of X*eta_charging,
        # which will have to be reversed during other time intervals in order
        # to keep the final SOC identical to the initial one. Since there is no
        # other way to decrease the SOC, the battery will charge and discharge
        # in the exact same measure (so as not to affect the external balance).
        # The charging and discharging power is given by the absolute value of:
        # X/((eta_charging-1/eta_discharging)/eta_charging)
        # On the the other hand, the surplus leading to the maximum power is:
        # max_power*((eta_charging-1/eta_discharging)/eta_charging)

        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(
            technologies.ElectricityGridConnection(working_rate=[1, 1, 1])
        )
        bs = BatteryStorage(
            name="bs",
            nominal_capacity=3,
            initial_soc=0.5,
            shared_limit=shared_limit,
            one_sense_per_time_step=mutex,
        )
        house_1.add(bs)

        house_1.add(
            demands.Electricity(
                name="electricity_demand",
                time_series=[1, 1, 1],
            )
        )

        # supply
        house_1.add(
            RenewableElectricitySource(
                name="renewable_electricity",
                nominal_power=1,
                specific_generation=[
                    1,
                    1 + surplus,  # causes an SOC increase of surplus*eta_chg
                    1,
                ],
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
        if expected_result is None:
            # infeasibility is expected: a warning will be raised
            with pytest.raises(RuntimeError):
                solved_model = solph_representation.solve(
                    solver=solver, solve_kwargs={"tee": False}
                )
            return
        solved_model = solph_representation.solve(
            solver=solver, solve_kwargs={"tee": False}
        )
        myresults = Results(solved_model)
        flows = myresults["flow"]
        label1 = ("distribution", "ElectricityCarrier", "house_1")
        label2 = ("Battery_Storage", "bs", "house_1")

        charging_power = flows[(str(label1), str(label2))]
        discharging_power = flows[(str(label2), str(label1))]

        mr = Results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=1e-3)

        if shared_limit:
            # with a shared limit, the amplitudes might change but not the dif.
            chg_dchg_diff = [0, surplus, 0]
            for i in range(len(chg_dchg_diff)):
                assert math.isclose(
                    chg_dchg_diff[i],
                    charging_power.iloc[i] - discharging_power.iloc[i],
                    abs_tol=1e-3,
                )
        else:
            # no shared limit: profiles can be tested
            for i in range(len(true_charging)):
                assert math.isclose(
                    charging_power.iloc[i], true_charging[i], abs_tol=1e-3
                )
                assert math.isclose(
                    discharging_power.iloc[i],
                    true_discharging[i],
                    abs_tol=1e-3,
                )
