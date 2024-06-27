"""This module provides Battery Storage"""

from oemof.solph import Flow
from oemof.solph.components import GenericStorage
from .._abstract_component import AbstractSolphRepresentation
from ._abstract_technology import AbstractTechnology
from ..carriers import ElectricityCarrier


class BatteryStorage(AbstractTechnology, AbstractSolphRepresentation):
    """Battery Storage Component"""

    def __init__(
        self,
        name: str,
        nominal_capacity: float,
        charging_C_Rate: float = 1,
        discharging_C_Rate: float = 1,
        charging_efficiency: float = 0.98,
        discharging_efficiency: float = 0.95,
        loss_rate: float = 0.0,
        initial_soc: float = 0.5,
        min_soc: float = 0.1,
    ):
        """
        Initialize Battery Storage.

        :param name: Name of the component
        :param nominal_capacity: Nominal capacity of the battery (in Wh)
        :param charging_C_Rate: Charging C-rate, default to 1
        :param discharging_C_Rate: Discharging C-rate, default to 1
        :param charging_efficiency: Efficiency during battery charging,
                                    default to 0.98.
        :param discharging_efficiency: Efficiency during battery discharging,
                                       default to 0.95.
        :param loss_rate: Loss rate of a battery storage, default to 0.
        :param initial_soc: Initial state of charge of a battery, default to 0.5.
        :param min_soc: Minimum state of charge of a battery, default to 0.1.
        """

        super().__init__(name=name)

        self.nominal_capacity = nominal_capacity
        self.charging_efficiency = charging_efficiency
        self.discharging_efficiency = discharging_efficiency
        self.charging_C_Rate = charging_C_Rate
        self.discharging_C_Rate = discharging_C_Rate
        self.loss_rate = loss_rate
        self.initial_soc = initial_soc
        self.min_soc = min_soc

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        electricity = self.location.get_carrier(ElectricityCarrier)

        self.create_solph_node(
            label="Battery_Storage",
            node_type=GenericStorage,
            inputs={
                electricity.distribution: Flow(
                    nominal_value=self.nominal_capacity * self.charging_C_Rate
                )
            },
            outputs={
                electricity.distribution: Flow(
                    nominal_value=self.nominal_capacity * self.discharging_C_Rate
                )
            },
            nominal_storage_capacity=self.nominal_capacity,
            loss_rate=self.loss_rate,
            min_storage_level=self.min_soc,
            initial_storage_level=self.initial_soc,
            inflow_conversion_factor=self.charging_efficiency,
            outflow_conversion_factor=self.discharging_efficiency,
        )
