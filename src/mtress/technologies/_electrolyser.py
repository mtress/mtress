"""This module provides hydrogen electrolyser."""

import logging
from dataclasses import dataclass
from typing import Optional

from oemof import solph
from oemof.solph import Flow, Investment
from oemof.solph.components import Converter, OffsetConverter

from .._helpers._util import enable_templating
from ..carriers import ElectricityCarrier, GasCarrier
from ..physics import HYDROGEN
from ._heater import AbstractHeater

from .._constants import EnergyType

LOGGER = logging.getLogger(__file__)


@dataclass(frozen=True)
class ElectrolyserTemplate:
    """
    Here we define the template for different electrolyser technologies
    (PEM, AEL, AEM) with their specific parameter values.
    Users can modify the parameter values (e.g. hydrogen production
    efficiency, thermal efficiency, etc.) for a particular technology
    type if needed or can create user-defined electrolyser technology.

    Important references on technologies:
    1. https://en.wikipedia.org/wiki/Polymer_electrolyte_membrane_electrolysis
    2. https://www.h-tec.com/produkte/detail/h-tec-pem-elektrolyseur-me450/me450/
    3. "Assessment of the Future Waste Heat Potential from Electrolysers and
    its Utilisation in District Heating" by Stefan REUTER, Ralf-Roman SCHMIDT
    4. "A study on the potential of excess heat from medium to large scale PEM
    electrolysis and the performance analysis of a dedicated cooling system"
    by W.J. Tiktak
    5. https://handbook.enapter.com/electrolyser/aem-flex120
    6. https://www.cummins.com/sites/default/files/2021-08/cummins-hystat-30-specsheet.pdf
    7. https://cellar-c2.services.clever-cloud.com/com-mcphy/uploads/2023/06/2023_McLyzer-Product-Line-EN.pdf
    8. https://nelhydrogen.com/product/atmospheric-alkaline-electrolyser-a-series/
    9. https://mart.cummins.com/imagelibrary/data/assetfiles/0070331.pdf
    10. https://hydrogen.johncockerill.com/en/products/electrolysers/

    """

    full_load_hydrogen_efficiency: float
    min_load_hydrogen_efficiency: float
    full_load_thermal_efficiency: float
    min_load_thermal_efficiency: float
    minimum_load: float
    maximum_temperature: float
    minimum_temperature: float
    hydrogen_output_pressure: float


# Efficiency for each of the technology are based on Lower Heating Value (LHV).
# The efficiency (hydrogen and thermal) assumed here are based on the Beginning
# of Life (BoL). In Practice, both the efficiency values of electrolyser
# changes as it gets older.

PEM_ELECTROLYSER = ElectrolyserTemplate(
    full_load_hydrogen_efficiency=0.63,
    min_load_hydrogen_efficiency=0.70,
    full_load_thermal_efficiency=0.25,
    min_load_thermal_efficiency=0.20,
    minimum_load=0.15,
    maximum_temperature=57,
    minimum_temperature=20,
    hydrogen_output_pressure=30,
)

ALKALINE_ELECTROLYSER = ElectrolyserTemplate(
    full_load_hydrogen_efficiency=0.66,
    min_load_hydrogen_efficiency=0.71,
    full_load_thermal_efficiency=0.20,
    min_load_thermal_efficiency=0.15,
    minimum_load=0.25,
    maximum_temperature=65,
    minimum_temperature=20,
    hydrogen_output_pressure=30,
)

AEM_ELECTROLYSER = ElectrolyserTemplate(
    full_load_hydrogen_efficiency=0.625,
    min_load_hydrogen_efficiency=0.71,
    full_load_thermal_efficiency=0.29,
    min_load_thermal_efficiency=0.20,
    minimum_load=0.30,
    maximum_temperature=50,
    minimum_temperature=20,
    hydrogen_output_pressure=35,
)


class AbstractElectrolyser(AbstractHeater):
    """
    Abstract class for electrolysers
    """

    def __init__(
        self,
        name: str,
        nominal_power: Investment | float,
        full_load_hydrogen_efficiency: float,
        full_load_thermal_efficiency: float,
        maximum_temperature: float,
        minimum_temperature: float,
        hydrogen_output_pressure: float,
    ):
        super().__init__(
            name=name,
            maximum_temperature=maximum_temperature,
            minimum_temperature=minimum_temperature,
        )
        self.nominal_power = nominal_power
        self.full_load_hydrogen_efficiency = full_load_hydrogen_efficiency
        self.full_load_thermal_efficiency = full_load_thermal_efficiency
        self.maximum_temperature = maximum_temperature
        self.minimum_temperature = minimum_temperature
        self.hydrogen_output_pressure = hydrogen_output_pressure

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        # Electrical connection
        self.electricity_carrier = self.location.get_carrier(
            ElectricityCarrier
        )
        self.electrical_bus = self.electricity_carrier.distribution

        # Hydrogen connection
        self.gas_carrier = self.location.get_carrier(GasCarrier)

        self.pressure, _ = self.gas_carrier.get_surrounding_levels(
            HYDROGEN, self.hydrogen_output_pressure
        )

        self.h2_bus = self.gas_carrier.inputs[HYDROGEN][self.pressure]

        # H2 output in kg at max load
        self.full_load_h2_output = (
            self.full_load_hydrogen_efficiency / HYDROGEN.LHV
        )


class Electrolyser(AbstractElectrolyser):
    """
    Electrolyser split water into hydrogen and oxygen with the electricity as
    input source of energy.Hydrogen can be used as an energy carrier for
    various applications. Excess heat from electrolyser (PEM, Alk, AEM) can
    also be utilised for space heating and hot water in: offices,
    commercial building, residential applications, either directly or via a
    district heating network. Heat requirement for Anaerobic Digestion (AD)
    Plant or some industrial processes can also be provided via Electrolysers.
    Waste heat utilisation can increase the system efficiency of up to 91 %.
    Oxygen produced in the electrolysis process is not considered in MTRESS.

    There are various types of electrolyser : PEM, Alkaline, AEM, etc.
    The SOEC is not considered in MTRESS. This class module can use
    electrolyser template for PEM, Alkaline, and AEM, with their default
    parameters as follows:

    from mtress.technologies import PEM_ELECTROLYSER

    house_1.add(
        technologies.Electrolyser(
            name="PEM",
            nominal_power=10e5,
            template=PEM_ELECTROLYSER
        )
    )

    but user can also overite the default parameters as per the requirements or
    user can ignore using the template and define all parameters manually.

    Note: This Electrolyser class do not consider the offset and partload
    operation of the electrolyser i.e., electrolyser operates at full load
    range with fixed efficiency and do not consider the part load operation.
    To consider partload operation please use OffsetElectrolyser class.
    """

    @enable_templating(ElectrolyserTemplate)
    def __init__(
        self,
        name: str,
        nominal_power: Investment | float,
        full_load_hydrogen_efficiency: float,
        full_load_thermal_efficiency: float,
        maximum_temperature: float,
        minimum_temperature: float,
        hydrogen_output_pressure: float,
    ):
        """
        Initialize Electrolyser

        :param name: Name of the component
        :param nominal_power: Nominal electrical power (in W) of the component
        :param full_load_hydrogen_efficiency: Hydrogen production efficiency at
            nominal load, i.e., the ratio of hydrogen output and
            electrical input
        :param full_load_thermal_efficiency: Thermal efficiency at the nominal
            load i.e., ratio of thermal output and electrical input
        :param maximum_temperature: Maximum waste heat temperature level
            (in °C).
        :param minimum_temperature: Minimum return temperature level (in °C)
        :param hydrogen_output_pressure: output pressure (in bar)
        """
        super().__init__(
            name=name,
            nominal_power=nominal_power,
            full_load_hydrogen_efficiency=full_load_hydrogen_efficiency,
            full_load_thermal_efficiency=full_load_thermal_efficiency,
            maximum_temperature=maximum_temperature,
            minimum_temperature=minimum_temperature,
            hydrogen_output_pressure=hydrogen_output_pressure,
        )

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        self.create_solph_node(
            label="electrolyser",
            node_type=Converter,
            inputs={
                self.electrical_bus: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    },
                    nominal_value=self.nominal_power,
                ),
            },
            outputs={
                self.h2_bus: Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.GAS,
                    }
                ),
                self.heat_bus: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    }
                ),
            },
            conversion_factors={
                self.electrical_bus: 1,
                self.h2_bus: self.full_load_h2_output,
                self.heat_bus: self.full_load_thermal_efficiency,
            },
        )


class OffsetElectrolyser(AbstractElectrolyser):
    """
    Electrolyser split water into hydrogen and oxygen with the electricity as
    input source of energy.Hydrogen can be used as an energy carrier for
    various applications. Excess heat from electrolyser (PEM, Alk, AEM) can
    also be utilised for space heating and hot water in: offices, commercial
    building, residential applications, either directly or via a district
    heating network. Heat requirement for Anaerobic Digestion (AD) Plant or
    some industrial processes can also be provided via Electrolysers.
    Waste heat utilisation can increase the system efficiency of up to 91 %.
    Oxygen produced in the electrolysis process is not considered in MTRESS.

    There are various types of electrolyser : PEM, Alkaline, AEM, etc.
    The SOEC is not considered in MTRESS. This class module can use
    electrolyser template for PEM, Alkaline, and AEM, with their default
    parameters as follows:

    from mtress.technologies import PEM_ELECTROLYSER

    house_1.add(
        technologies.OffsetElectrolyser(
            name="PEM",
            nominal_power=10e5,
            template=PEM_ELECTROLYSER
        )
    )

    but user can also overite the default parameters as per the requirements or
    user can ignore using the template and define all parameters manually.

    Note: This Electrolyser class consider the offsets and partload operation
    of the electrolyser.
    """

    @enable_templating(ElectrolyserTemplate)
    def __init__(
        self,
        name: str,
        nominal_power: Investment | float,
        full_load_hydrogen_efficiency: float,
        full_load_thermal_efficiency: float,
        maximum_temperature: float,
        minimum_temperature: float,
        hydrogen_output_pressure: float,
        min_load_hydrogen_efficiency: Optional[float] = None,
        min_load_thermal_efficiency: Optional[float] = None,
        minimum_load: Optional[float] = None,
        maximum_load: float = 1,
    ):
        """
        Initialize Electrolyser

        :param name: Name of the component
        :param nominal_power: Nominal electrical power (in W) of the component
        :param full_load_hydrogen_efficiency: Hydrogen production efficiency at
            nominal load, i.e., the ratio of hydrogen output and
            electrical input
        :param full_load_thermal_efficiency: Thermal efficiency at the nominal
            load i.e., ratio of thermal output and electrical input
        :param maximum_temperature: Maximum waste heat temperature level
            (in °C).
        :param minimum_temperature: Minimum return temperature level (in °C)
        :param hydrogen_output_pressure: Hydrogen output pressure (in bar)
        :param min_load_hydrogen_efficiency: Hydrogen production efficiency
            at minimum load.
        :param min_load_thermal_efficiency: Thermal efficiency at minimum load
        :param minimum_load: Minimum load level
            (fraction of the nominal/maximum load)
        :param maximum_load: Maximum load level, default is 1
        """
        super().__init__(
            name=name,
            nominal_power=nominal_power,
            full_load_hydrogen_efficiency=full_load_hydrogen_efficiency,
            full_load_thermal_efficiency=full_load_thermal_efficiency,
            minimum_temperature=minimum_temperature,
            maximum_temperature=maximum_temperature,
            hydrogen_output_pressure=hydrogen_output_pressure,
        )

        self.min_load_hydrogen_efficiency = min_load_hydrogen_efficiency
        self.min_load_thermal_efficiency = min_load_thermal_efficiency
        self.minimum_load = minimum_load
        self.maximum_load = maximum_load

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        min_load_h2_output = self.min_load_hydrogen_efficiency / HYDROGEN.LHV

        slope_h2, offset_h2 = (
            solph.components.slope_offset_from_nonconvex_input(
                self.maximum_load,
                self.minimum_load,
                self.full_load_h2_output,
                min_load_h2_output,
            )
        )

        slope_th, offset_th = (
            solph.components.slope_offset_from_nonconvex_input(
                self.maximum_load,
                self.minimum_load,
                self.full_load_thermal_efficiency,
                self.min_load_thermal_efficiency,
            )
        )

        self.create_solph_node(
            label="electrolyser",
            node_type=OffsetConverter,
            inputs={
                self.electrical_bus: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    },
                    nominal_value=self.nominal_power,
                    max=self.maximum_load,
                    min=self.minimum_load,
                    nonconvex=solph.NonConvex(),
                ),
            },
            outputs={
                self.h2_bus: Flow(
                    custom_properties={
                        "unit": "kg/h",
                        "energy_type": EnergyType.GAS,
                    },
                ),
                self.heat_bus: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.HEAT,
                    },
                ),
            },
            conversion_factors={
                self.h2_bus: slope_h2,
                self.heat_bus: slope_th,
            },
            normed_offsets={
                self.h2_bus: offset_h2,
                self.heat_bus: offset_th,
            },
        )
