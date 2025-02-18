"""This module covers Electric Vehicles"""

from oemof.solph import Flow
from oemof.solph.components import GenericStorage
from dataclasses import dataclass

from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ..carriers import ElectricityCarrier
from .._helpers._util import enable_templating
from ._battery_storage import BatteryStorage, BatteryStorageTemplate


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


        # if the EV is discharging, it cannot charge
        # if the EV is not plugged in, it cannot charge 
        # if the EV is plugged in, it can charge or discharge
        # therefore, there might be a conflict between the profiles
        # (plugged_in_profile and static_discharging_profile) which needs to be
        # sorted out

        BatteryStorage.__init__(self, **kwargs)

        # profiles
        self._plugged_in_profile = plugged_in_profile
        self._static_discharging_profile = static_discharging_profile

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        super().build_core()
        # TODO: implement model and constraints


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
