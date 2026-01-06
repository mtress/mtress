"""This module covers Electric Vehicles"""

from oemof.tools.debugging import ExperimentalFeatureWarning
from oemof.solph import Flow
from oemof.solph.components import GenericStorage
from dataclasses import dataclass
import warnings

from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ..carriers import ElectricityCarrier
from .._helpers._util import enable_templating
from ._battery_storage import BatteryStorage, BatteryStorageTemplate

from .._constants import EnergyType

from pandas import Series
from numbers import Real


@dataclass(frozen=True)
class ElectricVehicleTemplate(BatteryStorageTemplate):
    """
    A class for defining ElectricVehicle presets.

    :param name: Name of the component
    :param nominal_capacity: Nominal capacity of the battery (in Wh)
    :param charging_C_Rate: Charging C-rate
    :param discharging_C_Rate: Discharging C-rate
    :param charging_efficiency: Efficiency during battery charging
    :param discharging_efficiency: Efficiency during battery discharging
    :param loss_rate: Loss rate of a battery storage
    """

    consumption_per_distance: float  # unit: energy/distance


# Renault Zoe EV50 135HP
# source: https://www.adac.de/rund-ums-fahrzeug/autokatalog/marken-modelle/renault/zoe/1generation-facelift/325571/
GenericSegmentB_EV = ElectricVehicleTemplate(
    nominal_capacity=52e3,  # 52 kWh
    charging_C_Rate=50 / 52,  # 50 kW
    discharging_C_Rate=50 / 52,  # 50 kW
    charging_efficiency=0.95,  # 90% round trip?
    discharging_efficiency=0.95,  # 90% round trip?
    loss_rate=0,  # ?
    consumption_per_distance=0.174 * 1e3,  # 17.4 kWh/100km = 0.174 kWh/km
)

# Nissan Leaf
# source: https://www.adac.de/rund-ums-fahrzeug/autokatalog/marken-modelle/nissan/leaf/ze1/296708/
GenericSegmentC_EV = ElectricVehicleTemplate(
    nominal_capacity=62e3,  # 62 kWh
    charging_C_Rate=100 / 62,  # 100 kW
    discharging_C_Rate=100 / 62,  # 100 kW
    charging_efficiency=0.96,  # 90% round trip? used 96% for tests
    discharging_efficiency=0.95,  # 90% round trip?
    loss_rate=0,  # ?
    consumption_per_distance=0.178 * 1e3,  # 17.8 kWh/100km = 0.178 kWh/km
)


class GenericElectricVehicle(BatteryStorage):
    """
    Generic Electric Vehicle Component

    :param name: Name of the component
    :param nominal_capacity: Nominal capacity of the battery (in Wh)
    :param charging_C_Rate: Charging C-rate, default to 1
    :param discharging_C_Rate: Discharging C-rate, default to 1
    :param charging_efficiency: Efficiency during battery charging,
                                default to 0.98.
    :param discharging_efficiency: Efficiency during battery discharging,
                                   default to 0.95.
    :param loss_rate: Loss rate of a battery storage, default to 0.
    :param initial_soc: Initial state of charge of a battery,
        default to 0.5.
    :param min_soc: Minimum state of charge of a battery, default to 0.1.
    :param fixed_losses_absolute: numeric (iterable or scalar), losses per
        hour that are independent of storage content and independent of
        nominal storage capacity.
    :param one_sense_per_time_step: boolean, default to False, determines
        whether the model allows for charging and discharging within the
        same time interval (=False) or not (=True).
    :param shared_limit: boolean, default to True, limits the (average)
        charging and discharging power during a time interval to a given limit,
        defined as the average between the respective power limits. Please note
        this constraint is only introduced if charging and discharging can take
        place during the same time interval (one_sense_per_time_step=False).
    :param plugged_in_profile: A sequence of binary values indicating if
        the EV is plugged-in (=1) or not (=0). By default, the EV is
        permanently defined as being stationary, which means it can charge
        or discharge as long as power and SOC limits are observed.
    :param static_discharge_profile: A sequence of non-negative real values
        indicating the power delivered by the battery to the EV (and not to
        to the grid). Value errors will be raised if these values are in
        contradiction with the respective plugged-in status.
    """

    @enable_templating(BatteryStorageTemplate)
    def __init__(
        self,
        plugged_in_profile: TimeseriesSpecifier = 1,
        static_discharge_profile: TimeseriesSpecifier = 0.0,
        tolerance=1e-3,
        **kwargs,
    ):
        """Initialize Electric Vehicle instance."""
        warnings.warn(
            message="The EV class is untested and might jeild wrong resulds.",
            category=ExperimentalFeatureWarning,
        )

        # call super class constructor
        BatteryStorage.__init__(self, **kwargs)

        # check the inputs for compliance
        self.plugged_in_profile, self.static_discharge_profile = (
            self._validate_inputs(
                plugged_in_profile,
                static_discharge_profile,
                tolerance=tolerance,
            )
        )

        # combine the discharge profile with the losses
        self._combine_discharge_profile_losses(tolerance=tolerance)

    def _validate_inputs(
        self, plugged_in_profile, static_discharge_profile, tolerance=1e-3
    ):

        # things to keep in mind:
        # 1) mutually-exclusive charging and discharging:
        # - if the EV is discharging, it cannot charge
        # - if the EV is charging, it cannot discharge
        # 2) fixed discharge (due to driving)
        # - the fixed discharge cannot exceed the discharge rate
        # - the fixed discharge is equivalent to a grid load
        # 3) plugged-in status (applies per interval)
        # - if the EV is not plugged in, it cannot charge
        # - if the EV is not plugged in, it cannot discharge (to the grid)
        # - if the EV is plugged in, it can charge or discharge
        # - if the EV is plugged in, the fixed discharge has to be zero since
        # the (battery) absolute losses already cover any unavoidable losses

        if type(plugged_in_profile) == int and type(
            static_discharge_profile
        ) in [int, float]:
            # all are numeric

            # status values have to be binary
            if plugged_in_profile not in [0, 1]:
                raise ValueError(
                    "The EV's plugged-in status has to be 0 or 1."
                )

            # if not plugged in and the discharge is not zero, then error:
            # why? because otherwise the SOC will only decrease, as charging is
            # ruled out by the presence of a constant discharging profile

            if (
                plugged_in_profile != 1
                or abs(static_discharge_profile) > tolerance
            ):
                raise ValueError(
                    "This combination is not accepted, as it leads to "
                    + "infeasibility."
                )

        elif type(plugged_in_profile) in [list, tuple] and type(
            static_discharge_profile
        ) in [list, tuple]:
            # both are lists or tuples
            # sizes need to match
            if len(plugged_in_profile) != len(static_discharge_profile):
                raise ValueError("The profiles need to have the same size.")
            # status values have to be binary
            for value in plugged_in_profile:
                if not isinstance(value, Real):
                    raise TypeError(
                        "The EV's plugged-in status has to be 0 or 1."
                    )
                if value not in [0, 1]:
                    raise ValueError(
                        "The EV's plugged-in status has to be 0 or 1."
                    )
            # discharge values have to be non-negative
            # the static discharge profile cannot exceed the max dchg power
            for value in static_discharge_profile:
                if not isinstance(value, Real):
                    raise TypeError(
                        "Discharge profiles have to contain numeric data."
                    )
                if value < -tolerance:
                    raise ValueError(
                        "Discharge profile values cannot be negative."
                    )
                if value > self.nominal_capacity * self.discharging_C_Rate:
                    raise ValueError(
                        "The static discharge cannot exceed the maximum "
                        + "discharge rate."
                    )
            # if the EV is plugged in, the fixed discharge has to be zero
            for _sdp, _pip in zip(
                static_discharge_profile, plugged_in_profile
            ):
                if _pip == 1 and abs(_sdp) > tolerance:
                    raise ValueError(
                        "If the EV is plugged in, there can be no static "
                        + "discharge."
                    )

        elif (
            type(plugged_in_profile) == Series
            and type(static_discharge_profile) == Series
        ):
            # both are Series
            # sizes need to match
            if len(plugged_in_profile) != len(static_discharge_profile):
                raise ValueError("The profiles need to have the same size.")
            # status values have to be binary
            for idx in plugged_in_profile.index:
                if not isinstance(plugged_in_profile.loc[idx], Real):
                    raise TypeError(
                        "The EV's plugged-in status has to be 0 or 1."
                    )
                if plugged_in_profile.loc[idx] not in [0, 1]:
                    raise ValueError(
                        "The EV's plugged-in status has to be 0 or 1."
                    )
            # discharge values have to be non-negative
            # the static discharge profile cannot exceed the max dchg power
            for idx in static_discharge_profile.index:
                if not isinstance(static_discharge_profile.loc[idx], Real):
                    raise TypeError(
                        "Discharge profiles have to contain numeric data."
                    )
                if static_discharge_profile.loc[idx] < -tolerance:
                    raise ValueError(
                        "Discharge profile values cannot be negative."
                    )
                if (
                    static_discharge_profile.loc[idx]
                    > self.nominal_capacity * self.discharging_C_Rate
                ):
                    raise ValueError(
                        "The static discharge cannot exceed the maximum "
                        + "discharge rate."
                    )
            # if the EV is plugged in, the fixed discharge has to be zero
            for idx in plugged_in_profile.index:
                if (
                    plugged_in_profile.loc[idx] == 1
                    and abs(static_discharge_profile.loc[idx]) > tolerance
                ):
                    raise ValueError(
                        "If the EV is plugged in, there can be no static "
                        + "discharge."
                    )
        else:
            raise TypeError("Unsupported inputs.")
        # return the profiles
        return plugged_in_profile, static_discharge_profile

    def _combine_discharge_profile_losses(self, tolerance: float = 1e-3):

        # the ev is mobile if it is not always connected or does not discharge
        ev_is_mobile = not (
            # connected all the time
            (
                isinstance(self.plugged_in_profile, Real)
                and self.plugged_in_profile == 1
            )
            or (
                type(self.plugged_in_profile) in [Series, list, tuple]
                and all(self.plugged_in_profile)
            )
            # it never discharges
            or (
                isinstance(self.static_discharge_profile, Real)
                and abs(self.static_discharge_profile) <= tolerance
            )
            or (
                type(self.static_discharge_profile) in [Series, list, tuple]
                and not any(self.static_discharge_profile)
            )
        )

        # inputs are okay, process them if necessary
        if ev_is_mobile:
            # not stationary: losses need to be combined with the dchg. profile

            # losses: can be int, list/tuple or Series
            # profile: can be list/tuple or Series

            if isinstance(self.fixed_losses_absolute, Real):
                # has to be redefined
                if type(self.static_discharge_profile) in [list, tuple]:
                    self.fixed_losses_absolute = [
                        sdp / self.discharging_efficiency
                        + self.fixed_losses_absolute
                        for sdp in self.static_discharge_profile
                    ]
                else:
                    self.fixed_losses_absolute = (
                        self.static_discharge_profile
                        / self.discharging_efficiency
                        + self.fixed_losses_absolute
                    )

            elif type(self.fixed_losses_absolute) in [list, tuple]:
                # has to be redefined
                if type(self.static_discharge_profile) in [list, tuple]:
                    self.fixed_losses_absolute = [
                        sdp / self.discharging_efficiency + fla
                        for sdp, fla in zip(
                            self.static_discharge_profile,
                            self.fixed_losses_absolute,
                        )
                    ]
                else:
                    # static discharge profile is a Series
                    self.fixed_losses_absolute = (
                        self.static_discharge_profile
                        / self.discharging_efficiency
                        + Series(data=self.fixed_losses_absolute)
                    )
            else:  # series
                # has to be redefined
                if type(self.static_discharge_profile) in [list, tuple]:
                    self.fixed_losses_absolute = (
                        self.fixed_losses_absolute
                        + Series(data=self.static_discharge_profile)
                        / self.discharging_efficiency
                    )
                else:
                    # static discharge profile is a Series
                    self.fixed_losses_absolute = (
                        self.static_discharge_profile
                        / self.discharging_efficiency
                        + self.fixed_losses_absolute
                    )
        # stationary? no need to do anything else

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        electricity = self.location.get_carrier(ElectricityCarrier)

        self.thatbus = self.create_solph_node(
            label="EV",
            node_type=GenericStorage,
            inputs={
                electricity.distribution: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    },
                    nominal_value=self.nominal_capacity * self.charging_C_Rate,
                    max=self._solph_model.data.get_timeseries(
                        self.plugged_in_profile, kind=TimeseriesType.INTERVAL
                    ),
                )
            },
            outputs={
                electricity.distribution: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    },
                    nominal_value=self.nominal_capacity
                    * self.discharging_C_Rate,
                    max=self._solph_model.data.get_timeseries(
                        self.plugged_in_profile, kind=TimeseriesType.INTERVAL
                    ),
                )
            },
            nominal_storage_capacity=self.nominal_capacity,
            loss_rate=self.loss_rate,
            min_storage_level=self.min_soc,
            initial_storage_level=self.initial_soc,
            inflow_conversion_factor=self.charging_efficiency,
            outflow_conversion_factor=self.discharging_efficiency,
            fixed_losses_absolute=self._solph_model.data.get_timeseries(
                self.fixed_losses_absolute, kind=TimeseriesType.INTERVAL
            ),
        )


class ElectricVehicle(GenericElectricVehicle):
    """
    Electric Vehicle Component

    :param name: Name of the component
    :param nominal_capacity: Nominal capacity of the battery (in Wh)
    :param charging_C_Rate: Charging C-rate, default to 1
    :param discharging_C_Rate: Discharging C-rate, default to 1
    :param charging_efficiency: Efficiency during battery charging,
                                default to 0.98.
    :param discharging_efficiency: Efficiency during battery discharging,
                                   default to 0.95.
    :param loss_rate: Loss rate of a battery storage, default to 0.
    :param initial_soc: Initial state of charge of a battery,
        default to 0.5.
    :param min_soc: Minimum state of charge of a battery, default to 0.1.
    :param fixed_losses_absolute: numeric (iterable or scalar), losses per
        hour that are independent of storage content and independent of
        nominal storage capacity.
    :param consumption_per_distance: The energy consumption per distance
        travelled specific to this EV. The energy consumption represents
        that delivered to the EV, not the one seen from the point of view
        of the battery (before the discharge efficiency is considered).
    :param distance_travelled: A sequence of distances travelled with the
        EV. The parameter acts as an override for the static discharge
        profile. The units selected have to be consistent with those used
        with the consumption_per_distance parameter.
    :param one_sense_per_time_step: boolean, default to False, determines
        whether the model allows for charging and discharging within the
        same time interval (=False) or not (=True).
    :param shared_limit: boolean, default to True, limits the (average)
        charging and discharging power during a time interval to a given limit,
        defined as the average between the respective power limits. Please note
        this constraint is only introduced if charging and discharging can take
        place during the same time interval (one_sense_per_time_step=False).
    :param plugged_in_profile: A sequence of binary values indicating if
        the EV is plugged-in (=1) or not (=0). By default, the EV is
        permanently defined as being stationary, which means it can charge
        or discharge as long as power and SOC limits are observed.
    :param static_discharge_profile: A sequence of non-negative real values
        indicating the power delivered by the battery to the EV (and not to
        to the grid). Value errors will be raised if these values are in
        contradiction with the respective plugged-in status.
    """

    @enable_templating(ElectricVehicleTemplate)
    def __init__(
        self,
        consumption_per_distance: float,
        distance_travelled: TimeseriesSpecifier = 0.0,
        **kwargs,
    ):
        """Initialize Electric Vehicle instance."""

        # performance data
        self.consumption_per_distance = consumption_per_distance
        # create a static discharge profile based on the inputs
        if isinstance(distance_travelled, Real):
            # just a number
            static_discharge_profile = (
                consumption_per_distance * distance_travelled
            )
        elif type(distance_travelled) in [list, tuple]:
            static_discharge_profile = [
                consumption_per_distance * d for d in distance_travelled
            ]
        elif type(distance_travelled) == Series:
            static_discharge_profile = (
                distance_travelled * consumption_per_distance
            )
        else:
            raise TypeError("The inputs were not correctly specified.")

        if "static_discharge_profile" in kwargs:
            raise ValueError("The static discharge profile is redundant.")
        # replace the static discharging profile
        kwargs["static_discharge_profile"] = static_discharge_profile
        # create a connection status profile if it is not defined
        if "plugged_in_profile" not in kwargs and type(
            kwargs["static_discharge_profile"]
        ) in [list, tuple, Series]:

            # the default connection status profile was selected but a varying
            # static discharge profile was selected: create a new plugged-in
            # connection status profile to solve the conflict
            if type(kwargs["static_discharge_profile"]) in [list, tuple]:
                # list, tuple
                kwargs["plugged_in_profile"] = [
                    0 if sdp > 0 else 1
                    for sdp in kwargs["static_discharge_profile"]
                ]
            else:
                # Series
                kwargs["plugged_in_profile"] = Series(
                    data=[
                        0 if sdp > 0 else 1
                        for sdp in kwargs["static_discharge_profile"]
                    ]
                )

        # call super class constructor
        GenericElectricVehicle.__init__(self, **kwargs)
