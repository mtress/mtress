"""This module covers Electric Vehicles"""

from oemof.solph import Flow
from oemof.solph.components import GenericStorage
from dataclasses import dataclass

from .._data_handler import TimeseriesSpecifier, TimeseriesType
from .._abstract_component import AbstractSolphRepresentation
from ..carriers import ElectricityCarrier
from ._abstract_technology import AbstractTechnology
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
    pass
    
# EV1
EV1 = ElectricVehicleTemplate(
    nominal_capacity=6.4e3,         # 6.4 kWh
    charging_C_Rate=3.3/6.4,        # 3.3 kW
    discharging_C_Rate=3.3/6.4,     # 3.3 kW
    charging_efficiency=0.95,       # 95%
    discharging_efficiency=1/1.03,  # 100*(100/103) = ~97%
    loss_rate=0                     # ?
    )

# EV2
EV2 = ElectricVehicleTemplate(
    nominal_capacity=13.5e3,        # 1.5 kWh
    charging_C_Rate=5/13.5,         # 5 kW
    discharging_C_Rate=5/13.5,      # 5 kW
    charging_efficiency=0.95,       # 90% round trip = sqrt(0.9)*sqrt(0.9)
    discharging_efficiency=0.95,    # 90% round trip = sqrt(0.9)*sqrt(0.9)
    loss_rate=0                     # ?
    )

class ElectricVehicle(BatteryStorage):
    """Electric Vehicle Component"""

    @enable_templating(ElectricVehicleTemplate)
    def __init__(
        self,
        charging_availability: TimeseriesSpecifier = None,
        discharging_availability: TimeseriesSpecifier = None,
        static_charging_profile: TimeseriesSpecifier = None,   # if > 0: it is available for discharging too (stationary)
        static_discharging_profile: TimeseriesSpecifier = None, # if > 0: not available for charging (because it is moving)
        **kwargs
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

        BatteryStorage.__init__(
            self, 
            **kwargs
            )
        
        # profiles
        self.charging_availability = charging_availability
        self.discharging_availability = discharging_availability
        self.static_charging_profile = static_charging_profile
        self.static_discharging_profile = static_discharging_profile

    def build_core(self):
        """Build core structure of oemof.solph representation."""
                
        # carrier
        electricity = self.location.get_carrier(ElectricityCarrier)
        
        # create fixed demand profile
        self.create_solph_node(
            label="Electric_Vehicle",
            node_type=GenericStorage,
            inputs={
                electricity.distribution: Flow(
                    nominal_value=self.nominal_capacity * self.charging_C_Rate,
                    # max=self._solph_model.data.get_timeseries(
                    #     self.charging_availability*self.nominal_capacity,
                    #     kind=TimeseriesType.INTERVAL
                    # ),
                )
            },
            outputs={
                electricity.distribution: Flow(
                    nominal_value=self.nominal_capacity * self.discharging_C_Rate,
                    # max=self._solph_model.data.get_timeseries(
                    #     self.discharging_availability*self.nominal_capacity,
                    #     kind=TimeseriesType.INTERVAL
                    # ),
                )
            },
            nominal_storage_capacity=self.nominal_capacity,
            loss_rate=self.loss_rate,
            min_storage_level=self.min_soc,
            initial_storage_level=self.initial_soc,
            inflow_conversion_factor=self.charging_efficiency,
            outflow_conversion_factor=self.discharging_efficiency,
        )