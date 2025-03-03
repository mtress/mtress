"""This module covers Electric Vehicles"""

from oemof.solph import Flow
from oemof.solph.components import GenericStorage
from dataclasses import dataclass

from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ..carriers import ElectricityCarrier
from .._helpers._util import enable_templating
from ._battery_storage import BatteryStorage, BatteryStorageTemplate
from pandas import Series

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
        plugged_in_profile: TimeseriesSpecifier = None,
        static_discharging_profile: TimeseriesSpecifier = None,
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
        
        BatteryStorage.__init__(self, **kwargs)
        
        # TODO: process the discharge profile as if it is a grid-side load

        # profiles
        # plugged-in status
        self.plugged_in_profile = ( 
            1 
            if plugged_in_profile is None else 
            plugged_in_profile
            )
        # discharge profile
        self.static_discharging_profile = ( 
            0
            if static_discharging_profile is None else 
            static_discharging_profile
            ) 
        
        if type(self.plugged_in_profile) == int:
            
            if type(self.static_discharging_profile) in [int, float]:
                # if the EV is plugged in, the fixed discharge has to be zero
                if (self.plugged_in_profile and 
                    self.static_discharging_profile > 0):
                    raise ValueError(
                        'If the EV is plugged in, there can be no static '+
                        'discharge.'
                        )
                if (self.static_discharging_profile > 
                    self.nominal_capacity * self.discharging_C_Rate):
                    raise ValueError(
                        'The static discharge cannot exceed the maximum '+
                        'discharge rate.'
                        )
            elif type(self.static_discharging_profile) in [list,tuple]:
                # if the EV is plugged in, the fixed discharge has to be zero
                for _sdp in self.static_discharging_profile:
                    if self.plugged_in_profile == 1 and _sdp > 0:
                        raise ValueError(
                            'If the EV is plugged in, there can be no static '+
                            'discharge.'
                            )
                    if _sdp > self.nominal_capacity * self.discharging_C_Rate:
                        raise ValueError(
                            'The static discharge cannot exceed the maximum '+
                            'discharge rate.'
                            )
            elif type(self.static_discharging_profile) == Series:
                # if the EV is plugged in, the fixed discharge has to be zero
                for idx in self.static_discharging_profile.index:
                    if (self.plugged_in_profile == 1 and 
                        self.static_discharging_profile.loc[idx] > 0):
                        raise ValueError(
                            'If the EV is plugged in, there can be no static '+
                            'discharge.'
                            )
                    if (self.static_discharging_profile.loc[idx] > 
                        self.nominal_capacity * self.discharging_C_Rate):
                        raise ValueError(
                            'The static discharge cannot exceed the maximum '+
                            'discharge rate.'
                            )
            else:
                raise NotImplementedError
            
        elif type(self.plugged_in_profile) in [list, tuple]:
            
            if type(self.static_discharging_profile) in [int, float]:
                # if the EV is plugged in, the fixed discharge has to be zero
                for _pip in self.plugged_in_profile:
                    if _pip == 1 and self.static_discharging_profile > 0:
                        raise ValueError(
                            'If the EV is plugged in, there can be no static '+
                            'discharge.'
                            )
                    if (self.static_discharging_profile > 
                        self.nominal_capacity * self.discharging_C_Rate):
                        raise ValueError(
                            'The static discharge cannot exceed the maximum '+
                            'discharge rate.'
                            )
            elif type(self.static_discharging_profile) in [list,tuple]:
                # size
                if (len(self.plugged_in_profile) != 
                    len(self.static_discharging_profile)):
                    raise ValueError('The profiles have different sizes.') 
                # if the EV is plugged in, the fixed discharge has to be zero
                for _sdp, _pip in zip(
                        self.static_discharging_profile, 
                        self.plugged_in_profile
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
            elif type(self.static_discharging_profile) == Series:
                # size
                if (len(self.plugged_in_profile) != 
                    len(self.static_discharging_profile)):
                    raise ValueError('The profiles have different sizes.') 
                # if the EV is plugged in, the fixed discharge has to be zero
                for i, _pip in enumerate(self.plugged_in_profile):
                    if (_pip == 1 and
                        self.static_discharging_profile.iloc[i] > 0):
                        raise ValueError(
                            'If the EV is plugged in, there can be no static '+
                            'discharge.'
                            )
                    
                    if (self.static_discharging_profile.iloc[i] > 
                        self.nominal_capacity * self.discharging_C_Rate):
                        raise ValueError(
                            'The static discharge cannot exceed the maximum '+
                            'discharge rate.'
                            )
            else:
                raise NotImplementedError
    
        elif type(self.plugged_in_profile) == Series:
            
            if type(self.static_discharging_profile) in [int, float]:
                # if the EV is plugged in, the fixed discharge has to be zero
                for idx in self.plugged_in_profile.index:
                    if (self.plugged_in_profile.loc[idx] == 1 and
                        self.static_discharging_profile > 0):
                        raise ValueError(
                            'If the EV is plugged in, there can be no static '+
                            'discharge.'
                            )
                    if (self.static_discharging_profile > 
                        self.nominal_capacity * self.discharging_C_Rate):
                        raise ValueError(
                            'The static discharge cannot exceed the maximum '+
                            'discharge rate.'
                            )
            
            elif type(self.static_discharging_profile) in [list, tuple]:
                # sizes
                if (len(self.plugged_in_profile) != 
                    len(self.static_discharging_profile)):
                    raise ValueError('The profiles have different sizes.')
                # if the EV is plugged in, the fixed discharge has to be zero
                for i, _sdp in enumerate(self.static_discharging_profile):
                    if (self.plugged_in_profile.iloc[i] == 1 and
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
                
            elif type(self.static_discharging_profile) == Series:
                # sizes
                if (len(self.plugged_in_profile) != 
                    len(self.static_discharging_profile)):
                    raise ValueError('The profiles have different sizes.')
                # if the EV is plugged in, the fixed discharge has to be zero
                for idx in self.plugged_in_profile.index:
                    if (self.plugged_in_profile.loc[idx] == 1 and 
                        self.static_discharging_profile.loc[idx] > 0):
                        raise ValueError(
                            'If the EV is plugged in, there can be no static '+
                            'discharge.'
                            )
                    
                    if (self.static_discharging_profile.loc[idx] > 
                        self.nominal_capacity * self.discharging_C_Rate):
                        raise ValueError(
                            'The static discharge cannot exceed the maximum '+
                            'discharge rate.'
                            )

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
            fixed_losses_absolute=self.fixed_losses_absolute,
        )


class ElectricVehicle(GenericElectricVehicle):
    """Electric Vehicle Component"""

    @enable_templating(ElectricVehicleTemplate)
    def __init__(
        self,
        consumption_per_distance: float,
        distance_travelled: list = None,
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
        GenericElectricVehicle.__init__(self, **kwargs)

        # performance data
        self.consumption_per_distance = consumption_per_distance
        # prepare a list from the performance data and the profile
        self._static_discharging_profile = (
            [d * consumption_per_distance for d in distance_travelled]
            if distance_travelled is not None
            else None
        )
