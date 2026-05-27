from mtress.technologies import (
    ElectricVehicle,
    GenericElectricVehicle,
    GenericSegmentB_EV,
    GenericSegmentC_EV,
)
from mtress.technologies._ev import ElectricVehicleTemplate
from mtress.technologies import RenewableElectricitySource
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
from pandas import Series


@pytest.mark.skip(
    reason=(
        "Objecitve value seem to have changed. As the EV class is"
        " experimental, the issue might not be considered breaking."
    )
)
class TestGenericElectricVehicle:

    def check_ev_obj(
        self,
        ev: GenericElectricVehicle,
        template: ElectricVehicleTemplate,
        nominal_capacity=None,
        name="ev",
    ):
        assert ev.name == name
        assert (
            ev.nominal_capacity == template.nominal_capacity
            if nominal_capacity is None
            else ev.nominal_capacity == nominal_capacity
        )
        assert ev.charging_C_Rate == template.charging_C_Rate
        assert ev.discharging_C_Rate == template.discharging_C_Rate
        assert ev.charging_efficiency == template.charging_efficiency
        assert ev.discharging_efficiency == template.discharging_efficiency
        assert ev.loss_rate == template.loss_rate
        assert ev.consumption_per_distance == template.consumption_per_distance
        assert ev.fixed_losses_absolute == 0.0
        assert ev.static_discharge_profile == 0.0
        assert ev.plugged_in_profile == 1

    @staticmethod
    def result(
        template: ElectricVehicleTemplate,
        initial_soc=0.5,
        soc_max=1,
        prices=[50e-6, 5],
        loads=[150e3, 60e3],
        renewables=[0, 0],
        losses=[0, 0],
    ):

        return prices[0] * (
            loads[0]
            + (template.nominal_capacity * (soc_max - initial_soc) + losses[0])
            / (template.charging_efficiency)
            - renewables[0]
        ) + prices[1] * (
            loads[1]
            - (template.nominal_capacity * (soc_max - initial_soc) - losses[1])
            * template.discharging_efficiency
            - renewables[1]
        )

    @pytest.mark.parametrize(
        "template, renewable_generation, expected_result",
        [
            # results can be obtained with the result method
            (GenericSegmentB_EV, False, 176508.868421),
            (GenericSegmentB_EV, True, 176008.843421),
            (GenericSegmentC_EV, False, 152759.1145835),
            (GenericSegmentC_EV, True, 152259.0895835),
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
            technologies.ElectricityGridConnection(working_rate=prices)
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
                        ren / max(renewables) for ren in renewables
                    ],
                )
            )

        solph_representation = SolphModel(
            energy_system,
            timeindex=time_index,
        )

        solph_representation.build_solph_model()
        solved_model = solph_representation.solve(solve_kwargs={"tee": False})
        mr = Results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=1e-3)
        assert math.isclose(
            mr["objective"],
            self.result(
                template,
                renewables=renewables if renewable_generation else [0, 0],
            ),
            abs_tol=1e-3,
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
            _fix_losses = Series(data=_losses)
        else:  # float
            _losses = [fixed_losses, fixed_losses]
            _fix_losses = fixed_losses

        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(
            technologies.ElectricityGridConnection(working_rate=prices)
        )

        ev = GenericElectricVehicle(
            name="ev", fixed_losses_absolute=_fix_losses, template=template
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
        mr = Results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=1e-3)
        assert math.isclose(
            mr["objective"],
            self.result(template, losses=_losses),
            abs_tol=1e-3,
        )

    # *************************************************************************
    # *************************************************************************

    @staticmethod
    def other_result(
        template: ElectricVehicleTemplate,
        initial_soc=0.5,
        soc_max=1,
        prices=[50e-6, 50e-6, 5],
        loads=[0, 150e3, 60e3],
        renewables=[0, 0, 0],
        losses=[0, 0, 0],
        discharge=0,
    ):

        return (
            prices[0]
            * (
                loads[0]
                + (
                    template.nominal_capacity * (soc_max - initial_soc)
                    + losses[0]
                )
                / (template.charging_efficiency)
                - renewables[0]
            )
            + prices[1] * (loads[1])
            + prices[2]
            * (
                loads[2]
                - (
                    template.nominal_capacity * (soc_max - initial_soc)
                    - losses[2]
                    - discharge / template.discharging_efficiency
                )
                * template.discharging_efficiency
                - renewables[2]
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
            _discharge_profile = [0, discharge, 0]
            _connected_status_profile = [1, 0 if discharge > 0 else 1, 1]
        elif _type == Series:
            _discharge_profile = Series(data=[0, discharge, 0])
            _connected_status_profile = Series(
                data=[1, 0 if discharge > 0 else 1, 1]
            )

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
            technologies.ElectricityGridConnection(working_rate=prices)
        )

        ev = GenericElectricVehicle(
            name="ev",
            static_discharge_profile=_discharge_profile,
            plugged_in_profile=_connected_status_profile,
            template=template,
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
        solved_model = solph_representation.solve(solve_kwargs={"tee": False})
        mr = Results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=1e-3)
        assert math.isclose(
            mr["objective"],
            self.other_result(template, discharge=discharge),
            abs_tol=1e-3,
        )

    # *************************************************************************
    # *************************************************************************

    @pytest.mark.parametrize(
        "template, discharge, connected, loss, expected_result",
        [
            # lists, Real
            (
                GenericSegmentB_EV,
                [0, 1e3, 0],
                [1, 0, 1],
                1e3 * 2 / 3,
                187842.23850875002,
            ),
            # Series, Real
            (
                GenericSegmentB_EV,
                Series(data=[0, 1e3, 0]),
                Series(data=[1, 0, 1]),
                1e3 * 2 / 3,
                187842.23850875002,
            ),
            # lists, list
            (
                GenericSegmentB_EV,
                [0, 1e3, 0],
                [1, 0, 1],
                [0, 1e3, 1e3],
                191008.86842105,
            ),
            # lists, Series
            (
                GenericSegmentB_EV,
                [0, 1e3, 0],
                [1, 0, 1],
                Series(data=[0, 1e3, 1e3]),
                191008.86842105,
            ),
            # Series, lists
            (
                GenericSegmentB_EV,
                Series(data=[0, 1e3, 0]),
                Series(data=[1, 0, 1]),
                [0, 1e3, 1e3],
                191008.86842105,
            ),
            # Series, Series
            (
                GenericSegmentB_EV,
                Series(data=[0, 1e3, 0]),
                Series(data=[1, 0, 1]),
                Series(data=[0, 1e3, 1e3]),
                191008.86842105,
            ),
            # *****************************************************************
            # lists, Real
            (
                GenericSegmentB_EV,
                [0, 1e4, 0],
                [1, 0, 1],
                1e4 * 2 / 3,
                289842.55429825,
            ),
            # Series, Real
            (
                GenericSegmentB_EV,
                Series(data=[0, 1e4, 0]),
                Series(data=[1, 0, 1]),
                1e4 * 2 / 3,
                289842.55429825,
            ),
            # lists, list
            (
                GenericSegmentB_EV,
                [0, 1e4, 0],
                [1, 0, 1],
                [0, 1e4, 1e4],
                323831.58342105,
            ),
            # lists, Series
            (
                GenericSegmentB_EV,
                [0, 1e4, 0],
                [1, 0, 1],
                Series(data=[0, 1e4, 1e4]),
                323831.58342105,
            ),
            # Series, lists
            (
                GenericSegmentB_EV,
                Series(data=[0, 1e4, 0]),
                Series(data=[1, 0, 1]),
                [0, 1e4, 1e4],
                323831.58342105,
            ),
            # Series, Series
            (
                GenericSegmentB_EV,
                Series(data=[0, 1e4, 0]),
                Series(data=[1, 0, 1]),
                Series(data=[0, 1e4, 1e4]),
                323831.58342105,
            ),
            # *****************************************************************
            # lists, Real
            (
                GenericSegmentC_EV,
                [0, 1e3, 0],
                [1, 0, 1],
                1e3 * 2 / 3,
                164092.48430555002,
            ),
            # Series, Real
            (
                GenericSegmentC_EV,
                Series(data=[0, 1e3, 0]),
                Series(data=[1, 0, 1]),
                1e3 * 2 / 3,
                164092.48430555002,
            ),
            # lists, list
            (
                GenericSegmentC_EV,
                [0, 1e3, 0],
                [1, 0, 1],
                [0, 1e3, 1e3],
                167259.11458335,
            ),
            # lists, Series
            (
                GenericSegmentC_EV,
                [0, 1e3, 0],
                [1, 0, 1],
                Series(data=[0, 1e3, 1e3]),
                167259.11458335,
            ),
            # Series, lists
            (
                GenericSegmentC_EV,
                Series(data=[0, 1e3, 0]),
                Series(data=[1, 0, 1]),
                [0, 1e3, 1e3],
                167259.11458335,
            ),
            # Series, Series
            (
                GenericSegmentC_EV,
                Series(data=[0, 1e3, 0]),
                Series(data=[1, 0, 1]),
                Series(data=[0, 1e3, 1e3]),
                167259.11458335,
            ),
            # *****************************************************************
            # lists, Real
            (
                GenericSegmentC_EV,
                [0, 1e4, 0],
                [1, 0, 1],
                1e4 * 2 / 3,
                266092.79680555,
            ),
            # Series, Real
            (
                GenericSegmentC_EV,
                Series(data=[0, 1e4, 0]),
                Series(data=[1, 0, 1]),
                1e4 * 2 / 3,
                266092.79680555,
            ),
            # lists, list
            (
                GenericSegmentC_EV,
                [0, 1e4, 0],
                [1, 0, 1],
                [0, 1e4, 1e4],
                297759.11458335,
            ),
            # lists, Series
            (
                GenericSegmentC_EV,
                [0, 1e4, 0],
                [1, 0, 1],
                Series(data=[0, 1e4, 1e4]),
                297759.11458335,
            ),
            # Series, lists
            (
                GenericSegmentC_EV,
                Series(data=[0, 1e4, 0]),
                Series(data=[1, 0, 1]),
                [0, 1e4, 1e4],
                297759.11458335,
            ),
            # Series, Series
            (
                GenericSegmentC_EV,
                Series(data=[0, 1e4, 0]),
                Series(data=[1, 0, 1]),
                Series(data=[0, 1e4, 1e4]),
                297759.11458335,
            ),
            # *****************************************************************
        ],
    )
    def test_gev_profile_plus_losses(
        self, template, discharge, connected, loss, expected_result
    ):
        "Test a problem with non-stationary EV."
        # tests the static demand profile

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
            technologies.ElectricityGridConnection(working_rate=prices)
        )

        ev = GenericElectricVehicle(
            name="ev",
            static_discharge_profile=discharge,
            plugged_in_profile=connected,
            fixed_losses_absolute=loss,
            template=template,
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
        mr = Results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=1e-3)

    # *************************************************************************
    # *************************************************************************

    def test_trigger_errors(self):

        # # pending implementation error: mutex charging and discharging
        # with pytest.raises(NotImplementedError):
        #     GenericElectricVehicle(
        #         name="ev",
        #         static_discharge_profile=[1, 0, 1],
        #         plugged_in_profile=[0, 1, 0],
        #         fixed_losses_absolute=1e3,
        #         template=GenericSegmentB_EV,
        #         mutually_exclusive_charging_discharging=True
        #     )

        # unrecognised types: non-matching types
        with pytest.raises(TypeError):
            GenericElectricVehicle(
                name="ev",
                static_discharge_profile=Series(data=[1, 0, 1]),
                plugged_in_profile=[0, 1, 0],
                fixed_losses_absolute=1e3,
                template=GenericSegmentB_EV,
            )

        # lists with non-real types
        with pytest.raises(TypeError):
            GenericElectricVehicle(
                name="ev",
                static_discharge_profile=[1, 0, 1],
                plugged_in_profile=["0", 1, 0],
                fixed_losses_absolute=1e3,
                template=GenericSegmentB_EV,
            )
        with pytest.raises(TypeError):
            GenericElectricVehicle(
                name="ev",
                static_discharge_profile=["1", 0, 1],
                plugged_in_profile=[0, 1, 0],
                fixed_losses_absolute=1e3,
                template=GenericSegmentB_EV,
            )

        # Series with non-real types
        with pytest.raises(TypeError):
            GenericElectricVehicle(
                name="ev",
                static_discharge_profile=Series(data=[1, 0, 1]),
                plugged_in_profile=Series(data=["0", 1, 0]),
                fixed_losses_absolute=1e3,
                template=GenericSegmentB_EV,
            )
        with pytest.raises(TypeError):
            GenericElectricVehicle(
                name="ev",
                static_discharge_profile=Series(data=["1", 0, 1]),
                plugged_in_profile=Series(data=[0, 1, 0]),
                fixed_losses_absolute=1e3,
                template=GenericSegmentB_EV,
            )

    # *************************************************************************
    # *************************************************************************

    @pytest.mark.parametrize(
        "plugged_in_profile, static_discharge_profile",
        [
            # error: plugged-in and with static discharge
            # 1) int and int
            (1, 1),
            # 5) list and list
            ([1, 1, 1], [1000, 1000, 1000]),
            ([0, 0, 1], [0, 1000, 1000]),
            # 9) Series and Series
            (Series(data=[1, 1, 1]), Series(data=[0, 0, 1000])),
            (Series(data=[0, 0, 1]), Series(data=[1000, 1000, 1000])),
            # error: sizes do not match
            # 5) list and list
            ([1, 1, 1, 1], [1000, 1000, 1000]),
            ([0, 0, 1, 1], [0, 1000, 1000]),
            # 9) Series and Series
            (Series(data=[1, 1, 1, 1]), Series(data=[0, 0, 1000])),
            (Series(data=[0, 0, 1, 1]), Series(data=[1000, 1000, 1000])),
            # error: discharge rates exceed the maximum discharge rate
            # max rate: template.nominal_capacity*template.discharging_C_Rate
            # int, int
            (0, 1 + 52e3 * 50 / 52),
            # list, list
            ([0, 0], [0, 1 + 52e3 * 50 / 52]),
            # Series, Series
            (Series(data=[0, 0]), Series(data=[0, 1 + 52e3 * 50 / 52])),
            # error: trigger profile value errors
            # plugged in
            # int, int
            (-1, 52e3 * 50 / 52),
            (2, 0),
            # list, list
            ([2, 0], [0, 52e3 * 50 / 52]),
            ([1, -1], [0, 52e3 * 50 / 52]),
            # Series, Series
            (Series(data=[2, 0]), Series(data=[0, 52e3 * 50 / 52])),
            (Series(data=[1, -1]), Series(data=[0, 52e3 * 50 / 52])),
            # trigger value errors due to negative static discharge values
            # int, int
            (0, -1),
            # list, list
            ([0, 0], [-1, 1]),
            # Series, Series
            (Series(data=[0, 0]), Series(data=[-1, 1])),
            (Series(data=[2, 0]), Series(data=[0, 1])),
            (Series(data=[1, 0, -1]), Series(data=[0, 1, 0])),
            (Series(data=[1, 0, 1]), Series(data=[0, -1, 0])),
        ],
    )
    def test_trigger_profile_value_errors(
        self, plugged_in_profile, static_discharge_profile
    ):

        os.chdir(os.path.dirname(__file__))
        energy_system = MetaModel()
        house_1 = Location(name="house_1")
        energy_system.add_location(house_1)

        house_1.add(carriers.ElectricityCarrier())
        house_1.add(technologies.ElectricityGridConnection(working_rate=50e-6))

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
                loss_rate=0,
            )


# *****************************************************************************
# *****************************************************************************


@pytest.mark.skip(
    reason=(
        "Objecitve value seem to have changed. As the EV class is"
        " experimental, the issue might not be considered breaking."
    )
)
class TestElectricVehicle:

    # *************************************************************************
    # *************************************************************************

    @pytest.mark.parametrize(
        "template, distance, connected, loss, expected_result",
        [
            # lists, Real
            (
                GenericSegmentB_EV,
                [0, 1e3 / GenericSegmentB_EV.consumption_per_distance, 0],
                [1, 0, 1],
                1e3 * 2 / 3,
                187842.23850875002,
            ),
            # Series, Real
            (
                GenericSegmentB_EV,
                Series(
                    data=[
                        0,
                        1e3 / GenericSegmentB_EV.consumption_per_distance,
                        0,
                    ]
                ),
                Series(data=[1, 0, 1]),
                1e3 * 2 / 3,
                187842.23850875002,
            ),
            # lists, list
            (
                GenericSegmentB_EV,
                [0, 1e3 / GenericSegmentB_EV.consumption_per_distance, 0],
                [1, 0, 1],
                [0, 1e3, 1e3],
                191008.86842105,
            ),
            # lists, Series
            (
                GenericSegmentB_EV,
                [0, 1e3 / GenericSegmentB_EV.consumption_per_distance, 0],
                [1, 0, 1],
                Series(data=[0, 1e3, 1e3]),
                191008.86842105,
            ),
            # Series, lists
            (
                GenericSegmentB_EV,
                Series(
                    data=[
                        0,
                        1e3 / GenericSegmentB_EV.consumption_per_distance,
                        0,
                    ]
                ),
                Series(data=[1, 0, 1]),
                [0, 1e3, 1e3],
                191008.86842105,
            ),
            # Series, Series
            (
                GenericSegmentB_EV,
                Series(
                    data=[
                        0,
                        1e3 / GenericSegmentB_EV.consumption_per_distance,
                        0,
                    ]
                ),
                Series(data=[1, 0, 1]),
                Series(data=[0, 1e3, 1e3]),
                191008.86842105,
            ),
            # *****************************************************************
            # lists, Real
            (
                GenericSegmentB_EV,
                [0, 1e4 / GenericSegmentB_EV.consumption_per_distance, 0],
                [1, 0, 1],
                1e4 * 2 / 3,
                289842.55429825,
            ),
            # Series, Real
            (
                GenericSegmentB_EV,
                Series(
                    data=[
                        0,
                        1e4 / GenericSegmentB_EV.consumption_per_distance,
                        0,
                    ]
                ),
                Series(data=[1, 0, 1]),
                1e4 * 2 / 3,
                289842.55429825,
            ),
            # lists, list
            (
                GenericSegmentB_EV,
                [0, 1e4 / GenericSegmentB_EV.consumption_per_distance, 0],
                [1, 0, 1],
                [0, 1e4, 1e4],
                323831.58342105,
            ),
            # lists, Series
            (
                GenericSegmentB_EV,
                [0, 1e4 / GenericSegmentB_EV.consumption_per_distance, 0],
                [1, 0, 1],
                Series(data=[0, 1e4, 1e4]),
                323831.58342105,
            ),
            # Series, lists
            (
                GenericSegmentB_EV,
                Series(
                    data=[
                        0,
                        1e4 / GenericSegmentB_EV.consumption_per_distance,
                        0,
                    ]
                ),
                Series(data=[1, 0, 1]),
                [0, 1e4, 1e4],
                323831.58342105,
            ),
            # Series, Series
            (
                GenericSegmentB_EV,
                Series(
                    data=[
                        0,
                        1e4 / GenericSegmentB_EV.consumption_per_distance,
                        0,
                    ]
                ),
                Series(data=[1, 0, 1]),
                Series(data=[0, 1e4, 1e4]),
                323831.58342105,
            ),
            # *****************************************************************
            # lists, Real
            (
                GenericSegmentC_EV,
                [0, 1e3 / GenericSegmentC_EV.consumption_per_distance, 0],
                [1, 0, 1],
                1e3 * 2 / 3,
                164092.48430555002,
            ),
            # Series, Real
            (
                GenericSegmentC_EV,
                Series(
                    data=[
                        0,
                        1e3 / GenericSegmentC_EV.consumption_per_distance,
                        0,
                    ]
                ),
                Series(data=[1, 0, 1]),
                1e3 * 2 / 3,
                164092.48430555002,
            ),
            # lists, list
            (
                GenericSegmentC_EV,
                [0, 1e3 / GenericSegmentC_EV.consumption_per_distance, 0],
                [1, 0, 1],
                [0, 1e3, 1e3],
                167259.11458335,
            ),
            # lists, Series
            (
                GenericSegmentC_EV,
                [0, 1e3 / GenericSegmentC_EV.consumption_per_distance, 0],
                [1, 0, 1],
                Series(data=[0, 1e3, 1e3]),
                167259.11458335,
            ),
            # Series, lists
            (
                GenericSegmentC_EV,
                Series(
                    data=[
                        0,
                        1e3 / GenericSegmentC_EV.consumption_per_distance,
                        0,
                    ]
                ),
                Series(data=[1, 0, 1]),
                [0, 1e3, 1e3],
                167259.11458335,
            ),
            # Series, Series
            (
                GenericSegmentC_EV,
                Series(
                    data=[
                        0,
                        1e3 / GenericSegmentC_EV.consumption_per_distance,
                        0,
                    ]
                ),
                Series(data=[1, 0, 1]),
                Series(data=[0, 1e3, 1e3]),
                167259.11458335,
            ),
            # *****************************************************************
            # lists, Real
            (
                GenericSegmentC_EV,
                [0, 1e4 / GenericSegmentC_EV.consumption_per_distance, 0],
                [1, 0, 1],
                1e4 * 2 / 3,
                266092.79680555,
            ),
            # Series, Real
            (
                GenericSegmentC_EV,
                Series(
                    data=[
                        0,
                        1e4 / GenericSegmentC_EV.consumption_per_distance,
                        0,
                    ]
                ),
                Series(data=[1, 0, 1]),
                1e4 * 2 / 3,
                266092.79680555,
            ),
            # lists, list
            (
                GenericSegmentC_EV,
                [0, 1e4 / GenericSegmentC_EV.consumption_per_distance, 0],
                [1, 0, 1],
                [0, 1e4, 1e4],
                297759.11458335,
            ),
            # lists, Series
            (
                GenericSegmentC_EV,
                [0, 1e4 / GenericSegmentC_EV.consumption_per_distance, 0],
                [1, 0, 1],
                Series(data=[0, 1e4, 1e4]),
                297759.11458335,
            ),
            # Series, lists
            (
                GenericSegmentC_EV,
                Series(
                    data=[
                        0,
                        1e4 / GenericSegmentC_EV.consumption_per_distance,
                        0,
                    ]
                ),
                Series(data=[1, 0, 1]),
                [0, 1e4, 1e4],
                297759.11458335,
            ),
            # Series, Series
            (
                GenericSegmentC_EV,
                Series(
                    data=[
                        0,
                        1e4 / GenericSegmentC_EV.consumption_per_distance,
                        0,
                    ]
                ),
                Series(data=[1, 0, 1]),
                Series(data=[0, 1e4, 1e4]),
                297759.11458335,
            ),
            # *****************************************************************
        ],
    )
    def test_ev_profile_plus_losses(
        self, template, distance, connected, loss, expected_result
    ):
        "Test a problem with non-stationary EV."
        # tests the static demand profile

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
            technologies.ElectricityGridConnection(working_rate=prices)
        )

        ev = ElectricVehicle(
            name="ev",
            distance_travelled=distance,
            plugged_in_profile=connected,
            fixed_losses_absolute=loss,
            template=template,
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
        mr = Results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=1e-3)

    # *************************************************************************
    # *************************************************************************

    @pytest.mark.parametrize(
        "template, distance, loss, expected_result",
        [
            # lists, Real
            (
                GenericSegmentB_EV,
                [0, 1e3 / GenericSegmentB_EV.consumption_per_distance, 0],
                1e3 * 2 / 3,
                187842.23850875002,
            ),
            # Series, Real
            (
                GenericSegmentB_EV,
                Series(
                    data=[
                        0,
                        1e3 / GenericSegmentB_EV.consumption_per_distance,
                        0,
                    ]
                ),
                1e3 * 2 / 3,
                187842.23850875002,
            ),
            # lists, list
            (
                GenericSegmentB_EV,
                [0, 1e3 / GenericSegmentB_EV.consumption_per_distance, 0],
                [0, 1e3, 1e3],
                191008.86842105,
            ),
            # lists, Series
            (
                GenericSegmentB_EV,
                [0, 1e3 / GenericSegmentB_EV.consumption_per_distance, 0],
                Series(data=[0, 1e3, 1e3]),
                191008.86842105,
            ),
            # Series, lists
            (
                GenericSegmentB_EV,
                Series(
                    data=[
                        0,
                        1e3 / GenericSegmentB_EV.consumption_per_distance,
                        0,
                    ]
                ),
                [0, 1e3, 1e3],
                191008.86842105,
            ),
            # Series, Series
            (
                GenericSegmentB_EV,
                Series(
                    data=[
                        0,
                        1e3 / GenericSegmentB_EV.consumption_per_distance,
                        0,
                    ]
                ),
                Series(data=[0, 1e3, 1e3]),
                191008.86842105,
            ),
        ],
    )
    def test_ev_no_connection_profile(
        self, template, distance, loss, expected_result
    ):
        "Test a problem with non-stationary EV."
        # tests the static demand profile

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
            technologies.ElectricityGridConnection(working_rate=prices)
        )

        ev = ElectricVehicle(
            name="ev",
            distance_travelled=distance,
            fixed_losses_absolute=loss,
            template=template,
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
        solved_model = solph_representation.solve(solve_kwargs={"tee": False})
        mr = Results(solved_model)
        assert math.isclose(expected_result, mr["objective"], abs_tol=1e-3)

    # *************************************************************************
    # *************************************************************************

    def test_triggering_errors(self):

        # use improper inputs
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

        with pytest.raises(TypeError):
            ElectricVehicle(
                name="ev",
                distance_travelled={0: 1, 1: 2},  # use a dict
                template=GenericSegmentB_EV,
            )

        # provide the distance travelled and the static discharge profile
        with pytest.raises(ValueError):
            ElectricVehicle(
                name="ev",
                distance_travelled=[1, 2, 0],  # use a dict
                static_discharge_profile=[3, 2, 0],
                plugged_in_profile=[0, 0, 1],
                template=GenericSegmentB_EV,
            )


# *****************************************************************************
# *****************************************************************************
