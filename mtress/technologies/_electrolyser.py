"""This module provides hydrogen electrolyser."""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from oemof.solph import Flow
from oemof.solph.components import Converter

from .._abstract_component import AbstractSolphRepresentation
from .._helpers._util import enable_template
from ..carriers import Electricity, GasCarrier, Heat
from ..physics import HYDROGEN
from ._abstract_technology import AbstractTechnology

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
    3. "Assessment of the Future Waste Heat Potential from Electrolysers and its
    Utilisation in District Heating" by Stefan REUTER, Ralf-Roman SCHMIDT
    4. "A study on the potential of excess heat from medium­ to large­scale PEM
    electrolysis and the performance analysis of a dedicated cooling system"
    by W.J. Tiktak
    5. https://handbook.enapter.com/electrolyser/aem-flex120
    6. https://www.cummins.com/sites/default/files/2021-08/cummins-hystat-30-specsheet.pdf
    7. https://cellar-c2.services.clever-cloud.com/com-mcphy/uploads/2023/06/2023_McLyzer-Product-Line-EN.pdf
    8. https://nelhydrogen.com/product/atmospheric-alkaline-electrolyser-a-series/
    9. https://mart.cummins.com/imagelibrary/data/assetfiles/0070331.pdf
    10. https://hydrogen.johncockerill.com/en/products/electrolysers/


    """

    hydrogen_efficiency: float
    thermal_efficiency: float
    waste_heat_temperature: float
    hydrogen_output_pressure: float


#  Efficiency for each of the technology are based on Lower Heating Value (LHV).
#  The efficiency (hydrogen and thermal) assumed here are based on the Beginning
#  of Life (BoL). In Practice, both the efficiency values of electrolyser changes
#  as it gets older.

PEM_Electrolyser = ElectrolyserTemplate(
    hydrogen_efficiency=0.63,
    thermal_efficiency=0.25,
    waste_heat_temperature=57,
    hydrogen_output_pressure=30,
)

Alkaline_Electrolyser = ElectrolyserTemplate(
    hydrogen_efficiency=0.66,
    thermal_efficiency=0.20,
    waste_heat_temperature=65,
    hydrogen_output_pressure=30,
)

AEM_Electrolyser = ElectrolyserTemplate(
    hydrogen_efficiency=0.625,
    thermal_efficiency=0.29,
    waste_heat_temperature=50,
    hydrogen_output_pressure=35,
)


class Electrolyser(AbstractTechnology, AbstractSolphRepresentation):
    """
    Electrolyser split water into hydrogen and oxygen with the electricity as input
    source of energy. Hydrogen can be used as an energy carrier for various applications.
    Excess heat from low-temperature electrolyser (PEM, Alk, AEM) can also be utilised for
    space heating and hot water in: offices, commercial building, residential applications,
    either directly or via a district heating network. Heat requirement for Anaerobic Digestion
    (AD) Plant or some industrial processes can also be provided via Electrolysers. Waste heat
    utilisation can increase the system efficiency of up to 91 %. Oxygen produced in the
    electrolysis process is not considered in MTRESS.

    There are various types of electrolyser : PEM, Alkaline, AEM, etc. The SOEC technology is
    not yet considered in MTRESS. This class module takes PEM electrolyser as default technology,
    but user can select different technology type or can also user-defined their own technology
    as per the requirements.
    """

    @enable_template(ElectrolyserTemplate)
    def __init__(
        self,
        name: str,
        nominal_power: float,
        hydrogen_efficiency: float,
        thermal_efficiency: float,
        waste_heat_temperature: float,
        hydrogen_output_pressure: float,
    ):
        """
        Initialize Electrolyser

        :param name: Name of the component
        :param nominal_power: Nominal electrical power (kW) of the component
        :param hydrogen_efficiency: Hydrogen production efficiency of the electrolyser,
            i.e., the ratio of hydrogen output and electrical input
        :param thermal_efficiency: Thermal efficiency of the electrolyser,
            i.e., ratio of thermal output and electrical input
        :param waste_heat_temperature: Waste heat temperature level (°C).
        :param hydrogen_output_pressure: Hydrogen output pressure (bar)
        :param electrolyser_type: PEM_Electrolyser, or Alkaline_Electrolyser
            or AEM_Electrolyser. By default, it is PEM_Electrolyser.
        """
        super().__init__(name=name)

        self.nominal_power = nominal_power
        self.hydrogen_efficiency = hydrogen_efficiency
        self.thermal_efficiency = thermal_efficiency
        self.waste_heat_temperature = waste_heat_temperature
        self.hydrogen_output_pressure = hydrogen_output_pressure

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        # Electrical connection
        electricity_carrier = self.location.get_carrier(Electricity)
        electrical_bus = electricity_carrier.distribution

        # Hydrogen connection
        gas_carrier = self.location.get_carrier(GasCarrier)

        pressure, _ = gas_carrier.get_surrounding_levels(
            HYDROGEN, self.hydrogen_output_pressure
        )

        h2_bus = gas_carrier.inputs[HYDROGEN][pressure]

        # H2 output in kg
        h2_output = self.hydrogen_efficiency / HYDROGEN.LHV

        # Heat connection
        heat_carrier = self.location.get_carrier(Heat)

        temp_level, _ = heat_carrier.get_surrounding_levels(self.waste_heat_temperature)
        if np.isinf(temp_level):
            ValueError("No suitable temperature level available")

        if self.waste_heat_temperature - temp_level > 15:
            LOGGER.info(
                "Waste heat temperature significantly"
                "higher than suitable temperature level"
            )

        heat_bus = heat_carrier.inputs[temp_level]

        # TODO: Minimal power implementieren
        self.create_solph_node(
            label="converter",
            node_type=Converter,
            inputs={electrical_bus: Flow(nominal_value=self.nominal_power)},
            outputs={
                h2_bus: Flow(),
                heat_bus: Flow(),
            },
            conversion_factors={
                electrical_bus: 1,
                h2_bus: h2_output,
                heat_bus: self.thermal_efficiency,
            },
        )
