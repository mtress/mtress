"""This module provides fuel cell."""

import logging
from dataclasses import dataclass
import warnings

from oemof import solph
from oemof.solph import Flow, Investment
from oemof.solph.components import Converter, OffsetConverter

from .._helpers._util import enable_templating
from ..carriers import ElectricityCarrier, GasCarrier
from ..physics import HYDROGEN, Gas
from ._heater import AbstractHeater

from .._constants import EnergyType

LOGGER = logging.getLogger(__file__)


@dataclass(frozen=True)
class FuelCellTemplate:
    """
    Here we define the different fuel cell technologies (PEM, Alkaline, AEM)
    with their specific parameter values.

    Important references on technologies:
    1. "Hydrogen and fuel cell technologies for heating: A review"
        by Pual E. Dodds et. al.

    2. "Prospects of Fuel Cell Combined Heat and Power Systems"
        by AG. Olabi et. al.

    Users can modify the parameter values for a particular technology type
    if needed or can create user-defined fuel cell technology (e.g., SOFC, PFC,
    MCFC, etc.).
    """

    full_load_electrical_efficiency: float
    min_load_electrical_efficiency: float
    full_load_thermal_efficiency: float
    min_load_thermal_efficiency: float
    minimum_load: float
    maximum_temperature: float
    minimum_temperature: float
    gas_input_pressure: float


# Polymer Exchange Membrane Fuel Cell (PEMFC)
PEMFC = FuelCellTemplate(
    full_load_electrical_efficiency=0.36,
    min_load_electrical_efficiency=0.54,
    full_load_thermal_efficiency=0.50,
    min_load_thermal_efficiency=0.25,
    minimum_load=0.1,
    maximum_temperature=70,
    minimum_temperature=20,
    gas_input_pressure=80,
)

# Alkaline Fuel Cell (AFC)
AFC = FuelCellTemplate(
    full_load_electrical_efficiency=0.37,
    min_load_electrical_efficiency=0.534,
    full_load_thermal_efficiency=0.45,
    min_load_thermal_efficiency=0.18,
    minimum_load=0.25,
    maximum_temperature=65,
    minimum_temperature=20,
    gas_input_pressure=60,
)

#  Anion Exchange Membrane Fuel Cell (AEMFC)
AEMFC = FuelCellTemplate(
    full_load_electrical_efficiency=0.33,
    min_load_electrical_efficiency=0.52,
    full_load_thermal_efficiency=0.42,
    min_load_thermal_efficiency=0.27,
    minimum_load=0.25,
    maximum_temperature=55,
    minimum_temperature=20,
    gas_input_pressure=35,
)


class AbstractFuelCell(AbstractHeater):
    """
    Abstract base class for all Fuel Cell Technologies.
    """

    def __init__(
        self,
        name: str,
        nominal_power: float | Investment,
        full_load_electrical_efficiency: float,
        full_load_thermal_efficiency: float,
        maximum_temperature: float,
        minimum_temperature: float,
        gas_input_pressure: float,
        gas_type: Gas = HYDROGEN,
    ):
        super().__init__(
            name=name,
            maximum_temperature=maximum_temperature,
            minimum_temperature=minimum_temperature,
        )
        self.nominal_power = nominal_power
        self.full_load_electrical_efficiency = full_load_electrical_efficiency
        self.full_load_thermal_efficiency = full_load_thermal_efficiency
        self.gas_input_pressure = gas_input_pressure
        self.gas_type = gas_type

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        # Gas connection as an input to Fuel Cell
        self.gas_carrier = self.location.get_carrier(GasCarrier)

        _, self.pressure = self.gas_carrier.get_surrounding_levels(
            self.gas_type, self.gas_input_pressure
        )

        self.gas_bus = self.gas_carrier.inputs[self.gas_type][self.pressure]

        # Electrical connection for FC electrical output
        self.electricity_carrier = self.location.get_carrier(
            ElectricityCarrier
        )

        # Electrical efficiency with conversion from gas in kg
        # to electricity in W
        self.full_load_fuel_input = 1 / (
                    self.full_load_electrical_efficiency * self.gas_type.LHV)

        # thermal efficiency with conversion from gas in kg to heat in W.
        self.full_load_heat_output = (
            self.full_load_thermal_efficiency
            * self.gas_type.LHV
            * self.full_load_fuel_input
        )

        # electricity bus connection
        self.electricity_bus = self.electricity_carrier.distribution


class FuelCell(AbstractFuelCell):
    """
    Class for modeling a Fuel Cell (FC) technology.
    It inherits from AbstractFuelCell.

    Fuel cells converts chemical energy (hydrogen) to electricity, and
    potentially produces useful heat and water as byproducts. Fuel Cell could
    be used for various application to produce heat and power with hydrogen as
    fuel input. Hence, it enables better sector coupling between electricity
    and heating sector. They find widespread application in various sectors,
    especially stationary type fuel cell, such as backup power, distributed
    power generation, and co-generation, in the context of the
    MTRESS energy system.

    PEMFC are usually rated with electrical efficiency (@ LHV) of 35-39% and
    thermal efficiency (@ LHV) of ~20-55%. So, technically overall efficiency
    of 85-94% could be reached, if excess heat could be recovered. The excess
    heat could be recovered to increase the overall efficiency of the device.
    Operating temperature of low-temperature FC could range between 50-100 °C,
    making them suitable for space heating and boiling water for residential,
    commercial building, and/or industrial processes, etc. For instance, the
    H2home project demonstrated the use of PEMFC-based combined heat and power
    (CHP) systems for residential buildings. Ongoing research aims to push the
    operating temperature beyond 100 °C, with high-temperature PEMFCs
    (HT-PEMFCs) even capable of reaching up to 200 °C. Alternatively,
    high-temperature fuel cells like Solid Oxide Fuel Cells (SOFCs) operate at
    even higher temperatures, typically in the range of 500-1000 °C.  SOFCs are
    not considered in MTRESS yet. Fuel Cell CHP uses heat exchanger or heat
    recovery unit to harness heat energy to useful energy. Heat exchangers that
    circulates cooling liquid is used to extract heat for PEMFC, AFC, AEM
    and cathode air flow for SOFC.

    Overall, FC can offer promising solutions to our renewable-based
    energy system.

    There are various types of fuel cell (FC) technology : PEM, Alkaline,
    AEM, etc.
    This class module can use FC template (PEM, Alkaline, and AEM) with their
    default parameters as follows:

    from mtress.technologies import PEMFC

    house_1.add(
        technologies.FuelCell(
            name="PEMFC",
            nominal_power=10e5,
            template=PEMFC
        )
    )

    but user can also overite the default parameters as per the requirements or
    user can ignore using the template and define all parameters manually.
    Moreover its possible to change the input gas from Hydrogen to Methane or
    Biogas. By default the input gas is Hydrogen.

    Note: This FC class do not consider the offset and partload operation of
    the electrolyser i.e., electrolyser operates at full load range with fixed
    efficiency and do not consider the part load operation. To consider
    partload operation please use OffsetElectrolyser class.
    """

    @enable_templating(FuelCellTemplate)
    def __init__(
        self,
        name: str,
        nominal_power: float | Investment,
        full_load_electrical_efficiency: float,
        full_load_thermal_efficiency: float,
        maximum_temperature: float,
        minimum_temperature: float,
        gas_input_pressure: float,
        gas_type: Gas = HYDROGEN,
    ):
        """
        Initialize Fuel Cell (FC)

        :param name: Name of the component
        :param nominal_power: Nominal electrical power output of Fuel Cell (FC)
            (in W)
        :param full_load_electrical_efficiency: Electrical efficiency at
            max/nom load, i.e. ratio of electrical output and gas input
        :param full_load_thermal_efficiency: Thermal efficiency at the max/nom
            load, i.e. ratio of thermal output and gas input
        :param maximum_temperature: Maximum temperature (in °C) at which heat
            could be extracted from FC.
        :param minimum_temperature: Minimum return temperature level (in °C)
        :param gas_input_pressure: Pressure at which gas is injected to FC.
        :param gas_type: Input gas to FC, by default Hydrogen gas is used.
        """
        super().__init__(
            name=name,
            nominal_power=nominal_power,
            full_load_electrical_efficiency=full_load_electrical_efficiency,
            full_load_thermal_efficiency=full_load_thermal_efficiency,
            maximum_temperature=maximum_temperature,
            minimum_temperature=minimum_temperature,
            gas_input_pressure=gas_input_pressure,
            gas_type=gas_type,
        )

    def build_core(self):
        super().build_core()

        self.create_solph_node(
            label="fuel_cell",
            node_type=Converter,
            inputs={
                self.gas_bus: Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.GAS,
                    },
                ),
            },
            outputs={
                self.electricity_bus: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    },
                    nominal_value=self.nominal_power
                ),
                self.heat_bus: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    }
                ),
            },
            conversion_factors={
                self.gas_bus: self.full_load_fuel_input,
                self.electricity_bus: 1,
                self.heat_bus: self.full_load_heat_output,
            },
        )


class OffsetFuelCell(AbstractFuelCell):
    """
    Class for modeling a Fuel Cell (FC) technology.
    It inherits from AbstractFuelCell.

    Fuel cells converts chemical energy (hydrogen) to electricity, and
    potentially produces useful heat and water as byproducts. Fuel Cell could
    be used for various application to produce heat and power with hydrogen as
    fuel input. Hence, it enables better sector coupling between electricity
    and heating sector. They find widespread application in various sectors,
    especially stationary type fuel cell, such as backup power, distributed
    power generation, and co-generation, in the context of the
    MTRESS energy system.

    PEMFC are usually rated with electrical efficiency (@ LHV) of 35-39% and
    thermal efficiency (@ LHV) of ~20-55%. So, technically overall efficiency
    of 85-94% could be reached, if excess heat could be recovered. The excess
    heat could be recovered to increase the overall efficiency of the device.
    Operating temperature of low-temperature FC could range between 50-100 °C,
    making them suitable for space heating and boiling water for residential,
    commercial building, and/or industrial processes, etc. For instance, the
    H2home project demonstrated the usen of PEMFC-based combined heat and power
    (CHP) systems for residential buildings. Ongoing research aims to push the
    operating temperature beyond 100 °C, with high-temperature PEMFCs
    (HT-PEMFCs) even capable of reaching up to 200 °C. Alternatively,
    high-temperature fuel cells like Solid Oxide Fuel Cells (SOFCs) operate at
    even higher temperatures, typically in the range of 500-1000 °C.  SOFCs are
    not considered in MTRESS yet. Fuel Cell CHP uses heat exchanger or heat
    recovery unit to harness heat energy to useful energy. Heat exchangers that
    circulates cooling liquid is used to extract heat for PEMFC, AFC, AEM and
    cathode air flow for SOFC.

    Overall, FC can offer promising solutions to our renewable-based
    energy system.

    There are various types of fuel cell (FC) technology : PEM, Alkaline,
    AEM, etc.
    This class module can use FC template (PEM, Alkaline, and AEM) with their
    default parameters as follows:

    from mtress.technologies import PEMFC

    house_1.add(
        technologies.OffsetFuelCell(
            name="PEMFC",
            nominal_power=10e5,
            template=PEMFC
        )
    )

    but user can also overite the default parameters as per the requirements or
    user can ignore using the template and define all parameters manually.
    Moreover its possible to change the input gas from Hydrogen to Methane or
    Biogas. By default the input gas is Hydrogen.

    Note: This Fuel Cell class consider the offsets and partload operation.

    """

    @enable_templating(FuelCellTemplate)
    def __init__(
        self,
        name: str,
        nominal_power: float,
        full_load_electrical_efficiency: float,
        min_load_electrical_efficiency: float,
        full_load_thermal_efficiency: float,
        min_load_thermal_efficiency: float,
        minimum_load: float,
        maximum_temperature: float,
        minimum_temperature: float,
        gas_input_pressure: float,
        gas_type: Gas = HYDROGEN,
        maximum_load: float = 1,
    ):
        """
        Initialize Fuel Cell (FC)

        :param name: Name of the component
        :param nominal_power: Nominal electrical power output of Fuel Cell (FC)
            (in W)
        :param full_load_electrical_efficiency: Electrical efficiency at
            max/nom load, i.e. ratio of electrical output and gas input
        :param min_load_electrical_efficiency: Electrical efficiency at
            minimum load
        :param full_load_thermal_efficiency: Thermal efficiency at the max/nom
            load, i.e. ratio of thermal output and gas input
        :param min_load_thermal_efficiency: Thermal efficiency at the
            minimum load
        :param maximum_temperature: Maximum temperature (in °C) at which heat
            could be extracted from FC.
        :param minimum_temperature: Minimum return temperature level (in °C)
        :param gas_input_pressure: Pressure at which gas is injected to FC.
        :param gas_type: Input gas to FC, by default Hydrogen gas is used.

        :param min_load_thermal_efficiency: Thermal efficiency at minimum load
        :param minimum_load: Minimum load level
            (fraction of the nominal/maximum load)
        :param maximum_load: Maximum load level, default is 1
        """
        super().__init__(
            name=name,
            nominal_power=nominal_power,
            full_load_electrical_efficiency=full_load_electrical_efficiency,
            full_load_thermal_efficiency=full_load_thermal_efficiency,
            maximum_temperature=maximum_temperature,
            minimum_temperature=minimum_temperature,
            gas_input_pressure=gas_input_pressure,
            gas_type=gas_type,
        )

        self.min_load_electrical_efficiency = min_load_electrical_efficiency
        self.min_load_thermal_efficiency = min_load_thermal_efficiency
        self.minimum_load = minimum_load
        self.maximum_load = maximum_load

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        min_load_fuel_input = 1 / (
                    self.min_load_electrical_efficiency * self.gas_type.LHV)

        min_load_heat_output = ((self.min_load_thermal_efficiency *
                                self.gas_type.LHV) * min_load_fuel_input)

        # offset mode
        slope_gas, offset_gas = (
            solph.components.slope_offset_from_nonconvex_input(
                self.maximum_load,
                self.minimum_load,
                self.full_load_fuel_input,
                min_load_fuel_input,
            )
        )

        slope_ht, offset_ht = (
            solph.components.slope_offset_from_nonconvex_input(
                self.maximum_load,
                self.minimum_load,
                self.full_load_heat_output,
                min_load_heat_output,
            )
        )
        self.create_solph_node(
            label="fuel_cell",
            node_type=OffsetConverter,
            inputs={
                self.gas_bus: Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.GAS,
                    },
                ),
            },
            outputs={
                self.electricity_bus: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    },
                    nominal_value=self.nominal_power,
                    max=self.maximum_load,
                    min=self.minimum_load,
                    nonconvex=solph.NonConvex()
                ),
                self.heat_bus: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    }
                ),
            },
            conversion_factors={
                self.gas_bus: slope_gas,
                self.heat_bus: slope_ht,
            },
            normed_offsets={
                self.gas_bus: offset_gas,
                self.heat_bus: offset_ht,
            },
        )
