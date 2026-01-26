"""This module provides Battery Storage"""

from oemof.solph import Flow, Investment
from oemof.solph.components import GenericStorage
from dataclasses import dataclass
import pyomo.environ as pyo

from ..carriers import ElectricityCarrier
from ._abstract_technology import AbstractTechnology
from .._data_handler import TimeseriesSpecifier
from .._helpers._util import enable_templating

from .._constants import EnergyType


@dataclass(frozen=True)
class BatteryStorageTemplate:
    """
    A class for defining BatteryStorage presets.

    :param name: Name of the component
    :param nominal_capacity: Nominal capacity of the battery (in Wh)
    :param charging_C_Rate: Charging C-rate
    :param discharging_C_Rate: Discharging C-rate
    :param charging_efficiency: Efficiency during battery charging
    :param discharging_efficiency: Efficiency during battery discharging
    :param loss_rate: Loss rate of a battery storage
    """

    nominal_capacity: float | Investment
    charging_C_Rate: float
    discharging_C_Rate: float
    charging_efficiency: float
    discharging_efficiency: float
    loss_rate: float


# GenericBatteryModelI (source: https://doi.org/10.1109/SEST.2019.8849064)
GenericBatteryModelI = BatteryStorageTemplate(
    nominal_capacity=6.4e3,  # 6.4 kWh
    charging_C_Rate=3.3 / 6.4,  # 3.3 kW
    discharging_C_Rate=3.3 / 6.4,  # 3.3 kW
    charging_efficiency=0.95,  # 95%
    discharging_efficiency=1 / 1.03,  # 100*(100/103) = ~97%
    loss_rate=0,  # ?
)

# GenericBatteryModelII (source: PowerWall 2 datasheet)
GenericBatteryModelII = BatteryStorageTemplate(
    nominal_capacity=13.5e3,  # 1.5 kWh
    charging_C_Rate=5 / 13.5,  # 5 kW
    discharging_C_Rate=5 / 13.5,  # 5 kW
    charging_efficiency=0.95,  # 90% round trip = sqrt(0.9)*sqrt(0.9)
    discharging_efficiency=0.95,  # 90% round trip = sqrt(0.9)*sqrt(0.9)
    loss_rate=0,  # ?
)


class BatteryStorage(AbstractTechnology):
    """
    Battery Storage Component

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
    """

    @enable_templating(BatteryStorageTemplate)
    def __init__(
        self,
        name: str,
        nominal_capacity: float | Investment,
        charging_C_Rate: float = 1,
        discharging_C_Rate: float = 1,
        charging_efficiency: float = 0.98,
        discharging_efficiency: float = 0.95,
        loss_rate: float = 0.0,
        initial_soc: float = 0.5,
        min_soc: float = 0.1,
        fixed_losses_absolute: TimeseriesSpecifier = 0.0,
        one_sense_per_time_step: bool = False,
        shared_limit: bool = True,
    ):
        """
        Initialize Battery Storage.
        """

        super().__init__(name=name)

        if (shared_limit and isinstance(nominal_capacity, Investment)):
            raise NotImplementedError(
                "The 'shared_limit' is only implemented for fixed capacities."
            )
        if one_sense_per_time_step and shared_limit:
            # FIXME: It is a sign of a bad API that this is actually possible.
            raise AttributeError(
                "The arguments 'one_sense_per_time_step' and 'shared_limit' "
                + "are mutually exclusive."
            )

        self.nominal_capacity = nominal_capacity
        self.charging_efficiency = charging_efficiency
        self.discharging_efficiency = discharging_efficiency
        self.charging_C_Rate = charging_C_Rate
        self.discharging_C_Rate = discharging_C_Rate
        self.loss_rate = loss_rate
        self.initial_soc = initial_soc
        self.min_soc = min_soc
        self.fixed_losses_absolute = fixed_losses_absolute
        self.one_sense_per_time_step = one_sense_per_time_step
        self.shared_limit = shared_limit

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        electricity = self.location.get_carrier(ElectricityCarrier)

        if isinstance(self.nominal_capacity, Investment):
            inflow_capacity = Investment()
            outflow_capacity = Investment()
            invest_relation_input_capacity=self.charging_C_Rate,
            invest_relation_output_capacity=self.discharging_C_Rate,
        else:
            inflow_capacity = self.nominal_capacity * self.charging_C_Rate
            outflow_capacity = self.nominal_capacity * self.discharging_C_Rate
            invest_relation_input_capacity=None,
            invest_relation_output_capacity=None,

        self.battery_node = self.create_solph_node(
            label="Battery_Storage",
            node_type=GenericStorage,
            inputs={
                electricity.distribution: Flow(
                    nominal_capacity=inflow_capacity,
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    },
                ),
            },
            outputs={
                electricity.distribution: Flow(
                    nominal_capacity=outflow_capacity,
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    },
                ),
            },
            nominal_storage_capacity=self.nominal_capacity,
            loss_rate=self.loss_rate,
            min_storage_level=self.min_soc,
            initial_storage_level=self.initial_soc,
            inflow_conversion_factor=self.charging_efficiency,
            outflow_conversion_factor=self.discharging_efficiency,
            fixed_losses_absolute=self.fixed_losses_absolute,
            invest_relation_input_capacity=invest_relation_input_capacity,
            invest_relation_output_capacity=invest_relation_output_capacity,
        )

    def add_constraints(self):
        """Add constraints to the model."""
        electricity = self.location.get_carrier(ElectricityCarrier)

        if self.one_sense_per_time_step:
            # charging and discharging cannot happen during the same time step
            # >> use special ordered sets of type 1
            model = self._solph_model.model

            def rule_sos1_constraint(m, t):
                return [
                    m.flow[electricity.distribution, self.battery_node, t],
                    m.flow[self.battery_node, electricity.distribution, t],
                ]

            setattr(
                model,
                f"{self.node.label}_sos1_constraint",
                pyo.SOSConstraint(
                    model.TIMESTEPS, rule=rule_sos1_constraint, sos=1
                ),
            )
        else:
            # charging and discharging can happen during the same time step
            # >> apply a shared limit to reflect time dedicated to one or the
            # other (charging and discharging are mutually-exclusive, but both
            # can take place during the same time step)
            if self.shared_limit:
                model = self._solph_model.model

                def rule_shared_limit(m, t):
                    return (
                        # charging
                        m.flow[electricity.distribution, self.battery_node, t]
                        +
                        # discharging
                        m.flow[self.battery_node, electricity.distribution, t]
                    ) <= (
                        self.discharging_C_Rate + self.charging_C_Rate
                    ) * self.nominal_capacity / 2

                setattr(
                    model,
                    f"{self.node.label}_shared_limit",
                    pyo.Constraint(model.TIMESTEPS,
                                    rule=rule_shared_limit),
                )
