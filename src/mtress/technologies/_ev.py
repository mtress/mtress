"""This module covers Electric Vehicles"""

from oemof.solph import Flow
from oemof.solph.components import GenericStorage
from dataclasses import dataclass

from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ..carriers import ElectricityCarrier
from .._helpers._util import enable_templating
from ._battery_storage import BatteryStorage, BatteryStorageTemplate
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
    consumption_per_distance=0.174,  # 17.4 kWh/100km = 0.174 kWh/km
)

# Nissan Leaf
# source: https://www.adac.de/rund-ums-fahrzeug/autokatalog/marken-modelle/nissan/leaf/ze1/296708/
GenericSegmentC_EV = ElectricVehicleTemplate(
    nominal_capacity=62e3,  # 62 kWh
    charging_C_Rate=100 / 62,  # 100 kW
    discharging_C_Rate=100 / 62,  # 100 kW
    charging_efficiency=0.95,  # 90% round trip?
    discharging_efficiency=0.95,  # 90% round trip?
    loss_rate=0,  # ?
    consumption_per_distance=0.178,  # 17.8 kWh/100km = 0.178 kWh/km
)


class GenericElectricVehicle(BatteryStorage):
    """Electric Vehicle Component"""

    @enable_templating(ElectricVehicleTemplate)
    def __init__(
        self,
        plugged_in_profile: TimeseriesSpecifier = 1,
        static_discharge_profile: TimeseriesSpecifier = 0,
        **kwargs,
    ):
        """
        Initialize Electric Vehicle instance.

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
        """
        
        # call super class constructor
        BatteryStorage.__init__(self, **kwargs)

        # make sure the inputs are okay
        (self.plugged_in_profile, 
         self.static_discharge_profile) = self._check_inputs(
             plugged_in_profile, 
             static_discharge_profile
             )
        
        # combine the static_discharge_profile and the fixed_losses_absolute
        if (type(self.static_discharge_profile) != 
            type(self.fixed_losses_absolute)):
            # different types
            if self.static_discharge_profile == 0:
                # no static discharge: just use the fixed losses
                self.final_discharge_profile = self.fixed_losses_absolute
            elif self.fixed_losses_absolute == 0:
                # no fixed losses: just use the static discharge profile
                self.final_discharge_profile = (
                    self.static_discharge_profile
                    )
            else:
                raise TypeError(
                    'Profiles should be defined using the same type.'
                    )
        elif isinstance(self.static_discharge_profile, Real):
            # both are Real numbers: just sum them
            self.final_discharge_profile = (
                self.static_discharge_profile+self.fixed_losses_absolute
                )
        elif type(self.static_discharge_profile) in [tuple, list]:
            # both are list/tuples: just sum their elements one by one
            self.final_discharge_profile = [
                a+b
                for a, b in zip(
                        self.static_discharge_profile, 
                        self.fixed_losses_absolute
                        )
                ]
        elif type(self.static_discharge_profile) == Series:
            # both are Series: just sum their elements one by one
            self.final_discharge_profile = (
                self.static_discharge_profile+self.fixed_losses_absolute
                )
        else:
            raise NotImplementedError
             
        # TODO: process the discharge profile as if it is a grid-side load
        
        # TODO: check for sign errors
        
    def _check_inputs(self, plugged_in_profile, static_discharge_profile):
        
        # things to keep in mind:
        # 1) mutually-exclusive charging and discharging:
        # - if the EV is discharging, it cannot charge
        # - if the EV is charging, it cannot discharge
        # 2) fixed discharge (due to driving)
        # - the fixed discharge cannot exceed the discharge rate
        # - the fixed discharge is equivalent to a grid load
        # 3) plugged-in status
        # - if the EV is not plugged in, it cannot charge 
        # - if the EV is not plugged in, it cannot discharge (to the grid)
        # - if the EV is plugged in, it can charge or discharge
        # - if the EV is plugged in, the fixed discharge has to be zero
        
        if type(plugged_in_profile) == int:
            # check the profile data
            if plugged_in_profile not in [0, 1]:
                raise ValueError(
                    'The EV\'s plugged-in status has to be 0 or 1.'
                    )
            # check the data for logic
            if type(static_discharge_profile) in [int, float]:
                # discharge values have to be non-negative
                if static_discharge_profile < 0:
                    raise ValueError(
                        'Discharge profile values cannot be negative.'
                        )
                # if the EV is plugged in, the fixed discharge has to be zero
                if (plugged_in_profile and 
                    static_discharge_profile > 0):
                    raise ValueError(
                        'If the EV is plugged in, there can be no static '+
                        'discharge.'
                        )
                if (static_discharge_profile > 
                    self.nominal_capacity * self.discharging_C_Rate):
                    raise ValueError(
                        'The static discharge cannot exceed the maximum '+
                        'discharge rate.'
                        )
            elif type(static_discharge_profile) in [list,tuple]:
                # if the EV is plugged in, the fixed discharge has to be zero
                for _sdp in static_discharge_profile:
                    if plugged_in_profile == 1 and _sdp > 0:
                        raise ValueError(
                            'If the EV is plugged in, there can be no static '+
                            'discharge.'
                            )
                    if _sdp > self.nominal_capacity * self.discharging_C_Rate:
                        raise ValueError(
                            'The static discharge cannot exceed the maximum '+
                            'discharge rate.'
                            )
                    if _sdp < 0:
                        raise ValueError(
                            'Discharge profile values cannot be negative.'
                            )
            elif type(static_discharge_profile) == Series:
                # if the EV is plugged in, the fixed discharge has to be zero
                for idx in static_discharge_profile.index:
                    if (plugged_in_profile == 1 and 
                        static_discharge_profile.loc[idx] > 0):
                        raise ValueError(
                            'If the EV is plugged in, there can be no static '+
                            'discharge.'
                            )
                    if (static_discharge_profile.loc[idx] > 
                        self.nominal_capacity * self.discharging_C_Rate):
                        raise ValueError(
                            'The static discharge cannot exceed the maximum '+
                            'discharge rate.'
                            )
                    if static_discharge_profile.loc[idx] < 0:
                        raise ValueError(
                            'Discharge profile values cannot be negative.'
                            )
            else:
                raise TypeError(
                    'Unsupported type for the static discharge profile.'
                    )
            
        elif type(plugged_in_profile) in [list, tuple]:
            # check the profile data
            for value in plugged_in_profile:
                if type(value) != int:
                    raise TypeError('The values should be integers.')
                if value not in [0, 1]:
                    raise ValueError(
                        'The EV\'s plugged-in status has to be 0 or 1.'
                        )
            # check the data for logic
            if type(static_discharge_profile) in [int, float]:
                # discharge values have to be non-negative
                if static_discharge_profile < 0:
                    raise ValueError(
                        'Discharge profile values cannot be negative.'
                        )
                # if the EV is plugged in, the fixed discharge has to be zero
                for _pip in plugged_in_profile:
                    if _pip == 1 and static_discharge_profile > 0:
                        raise ValueError(
                            'If the EV is plugged in, there can be no static '+
                            'discharge.'
                            )
                    if (static_discharge_profile > 
                        self.nominal_capacity * self.discharging_C_Rate):
                        raise ValueError(
                            'The static discharge cannot exceed the maximum '+
                            'discharge rate.'
                            )
            elif type(static_discharge_profile) in [list,tuple]:
                # size
                if (len(plugged_in_profile) != 
                    len(static_discharge_profile)):
                    raise ValueError('The profiles have different sizes.') 
                # if the EV is plugged in, the fixed discharge has to be zero
                for _sdp, _pip in zip(
                        static_discharge_profile, 
                        plugged_in_profile
                        ):
                    if _pip == 1 and _sdp > 0:
                        raise ValueError(
                            'If the EV is plugged in, there can be no static '+
                            'discharge.'
                            )
                    if _sdp > self.nominal_capacity * self.discharging_C_Rate:
                        raise ValueError(
                            'The static discharge cannot exceed the maximum '+
                            'discharge rate.'
                            )
                    if _sdp < 0:
                        raise ValueError(
                            'Discharge profile values cannot be negative.'
                            )
            elif type(static_discharge_profile) == Series:
                # size
                if (len(plugged_in_profile) != 
                    len(static_discharge_profile)):
                    raise ValueError('The profiles have different sizes.') 
                # if the EV is plugged in, the fixed discharge has to be zero
                for i, _pip in enumerate(plugged_in_profile):
                    if (_pip == 1 and
                        static_discharge_profile.iloc[i] > 0):
                        raise ValueError(
                            'If the EV is plugged in, there can be no static '+
                            'discharge.'
                            )
                    
                    if (static_discharge_profile.iloc[i] > 
                        self.nominal_capacity * self.discharging_C_Rate):
                        raise ValueError(
                            'The static discharge cannot exceed the maximum '+
                            'discharge rate.'
                            )
                    if static_discharge_profile.iloc[i] < 0:
                        raise ValueError(
                            'Discharge profile values cannot be negative.'
                            )
            else:
                raise TypeError(
                    'Unsupported type for the static discharge profile.'
                    )
    
        elif type(plugged_in_profile) == Series:
            # check the profile data
            for value in plugged_in_profile:
                if type(value) != int:
                    raise TypeError('The values should be integers.')
                if value not in [0, 1]:
                    raise ValueError(
                        'The EV\'s plugged-in status has to be 0 or 1.'
                        )
            
            if type(static_discharge_profile) in [int, float]:
                # discharge values have to be non-negative
                if static_discharge_profile < 0:
                    raise ValueError(
                        'Discharge profile values cannot be negative.'
                        )
                # if the EV is plugged in, the fixed discharge has to be zero
                for idx in plugged_in_profile.index:
                    if (plugged_in_profile.loc[idx] == 1 and
                        static_discharge_profile > 0):
                        raise ValueError(
                            'If the EV is plugged in, there can be no static '+
                            'discharge.'
                            )
                    if (static_discharge_profile > 
                        self.nominal_capacity * self.discharging_C_Rate):
                        raise ValueError(
                            'The static discharge cannot exceed the maximum '+
                            'discharge rate.'
                            )
            
            elif type(static_discharge_profile) in [list, tuple]:
                # sizes
                if (len(plugged_in_profile) != 
                    len(static_discharge_profile)):
                    raise ValueError('The profiles have different sizes.')
                # if the EV is plugged in, the fixed discharge has to be zero
                for i, _sdp in enumerate(static_discharge_profile):
                    if (plugged_in_profile.iloc[i] == 1 and
                        _sdp > 0):
                        raise ValueError(
                            'If the EV is plugged in, there can be no static '+
                            'discharge.'
                            )
                    if _sdp > self.nominal_capacity * self.discharging_C_Rate:
                        raise ValueError(
                            'The static discharge cannot exceed the maximum '+
                            'discharge rate.'
                            )
                    if _sdp < 0:
                        raise ValueError(
                            'Discharge profile values cannot be negative.'
                            )
                
            elif type(static_discharge_profile) == Series:
                # sizes
                if (len(plugged_in_profile) != 
                    len(static_discharge_profile)):
                    raise ValueError('The profiles have different sizes.')
                # if the EV is plugged in, the fixed discharge has to be zero
                for idx in plugged_in_profile.index:
                    if (plugged_in_profile.loc[idx] == 1 and 
                        static_discharge_profile.loc[idx] > 0):
                        raise ValueError(
                            'If the EV is plugged in, there can be no static '+
                            'discharge.'
                            )
                    
                    if (static_discharge_profile.loc[idx] > 
                        self.nominal_capacity * self.discharging_C_Rate):
                        raise ValueError(
                            'The static discharge cannot exceed the maximum '+
                            'discharge rate.'
                            )
                    if static_discharge_profile.loc[idx] < 0:
                        raise ValueError(
                            'Discharge profile values cannot be negative.'
                            )
            
            else:
                raise TypeError(
                    'Unsupported type for the static discharge profile.'
                    )
        else:
            raise TypeError('Unsupported type for the plugged-in profile.')
        # return the profiles
        return plugged_in_profile, static_discharge_profile

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        # super().build_core()
        # TODO: mutually-exclusive charging and discharging
        
        electricity = self.location.get_carrier(ElectricityCarrier)
        
        self.create_solph_node(
            label="EV",
            node_type=GenericStorage,
            inputs={
                electricity.distribution: Flow(
                    nominal_value=self.nominal_capacity * self.charging_C_Rate,
                    max=self._solph_model.data.get_timeseries(
                        self.plugged_in_profile, 
                        kind=TimeseriesType.INTERVAL
                    ),
                )
            },
            outputs={
                electricity.distribution: Flow(
                    nominal_value=self.nominal_capacity
                    * self.discharging_C_Rate,
                    max=self._solph_model.data.get_timeseries(
                        self.plugged_in_profile, 
                        kind=TimeseriesType.INTERVAL
                    )
                )
            },
            nominal_storage_capacity=self.nominal_capacity,
            loss_rate=self.loss_rate,
            min_storage_level=self.min_soc,
            initial_storage_level=self.initial_soc,
            inflow_conversion_factor=self.charging_efficiency,
            outflow_conversion_factor=self.discharging_efficiency,
            fixed_losses_absolute=self.final_discharge_profile
        )


class ElectricVehicle(GenericElectricVehicle):
    """Electric Vehicle Component"""

    @enable_templating(ElectricVehicleTemplate)
    def __init__(
        self,
        consumption_per_distance: float,
        distance_travelled: TimeseriesSpecifier = 0.0,
        **kwargs,
    ):
        """
        Initialize Electric Vehicle instance.

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
        """
        
        # performance data
        self.consumption_per_distance = consumption_per_distance
        
        if isinstance(distance_travelled, Real):
            static_discharge_profile = (
                consumption_per_distance*distance_travelled
                )
        elif type(distance_travelled) in [list, tuple]:
            static_discharge_profile = [
                consumption_per_distance*d
                for d in distance_travelled
                ]
        elif type(distance_travelled) == Series:
            static_discharge_profile = (
                distance_travelled*consumption_per_distance
                )
        else:
            raise TypeError('The inputs were not correctly specified.')
        
        # if 'static_discharge_profile' in kwargs:
        #     raise Warning(
        #         'The value for the static discharge profile is '+
        #         'being overwritten.'
        #         )
        
        kwargs['static_discharge_profile'] = static_discharge_profile
        # call super class constructor
        GenericElectricVehicle.__init__(
            self, 
            **kwargs
            )

