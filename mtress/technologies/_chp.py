"""This module provides combined heat and power (CHP)"""

import logging
from dataclasses import dataclass

import numpy as np
from oemof.solph import Flow
from oemof.solph.components import Converter

from .._abstract_component import AbstractSolphRepresentation
from .._helpers._util import enable_templating
from ..carriers import Electricity, GasCarrier, HeatCarrier
from ..physics import BIO_METHANE, BIOGAS, HYDROGEN, NATURAL_GAS, Gas
from ._abstract_technology import AbstractTechnology

LOGGER = logging.getLogger(__file__)


@dataclass(frozen=True)
class CHPTemplate:
    """
    Template for combined heat and power (CHP) technologies with
    different gases or gas mixtures as fuel input. The templates
    include various options such as: NATURALGAS_CHP, BIOGAS_CHP,
    BIOMETHANE_CHP, HYDROGEN_CHP, HYDROGEN_CHP, HYDROGEN_MIXED_CHP.
    The naming convention for these templates is based on the fuel
    input followed by CHP, with underscores in between the words.
    For example, NATURALGAS_CHP indicates a CHP technology that
    uses natural gas as fuel. Parametric values of the CHP techno-
    -logies defined here are typically based on gas turbine or
    reciprocating engine type. Thermal and electrical efficiencies
    differs with the size of the CHP, therefore, 500 kW electrical
    nominal capacity is considered, as a base size, for each technology,
    to provide default efficiency values. Users are recommended to
    change the efficiency values based on their use-case.

    Note: User can either select one of the default template with the
    possibility of changing the parameter values, or create new user-
    -defined technology. Moreover, in the variable gas_type, user must
    provide gas/gases with their respective share/s in vol %, if default
    template is not selected.

    Important references for technologies:
    1. https://gentec.cz/en/cogeneration-units/
    2. https://www.innio.com/images/medias/files/5092/innio_cs_hansewerknatur_en_screen_ijb-422035-en.pdf
    3. https://www.jenbacher.com/en/energy-solutions/energy-sources/hydrogen
    4. https://www.clarke-energy.com/chp-cogeneration/
    5. https://www.clarke-energy.com/gas-engines/
    6. https://www.jenbacher.com/en/gas-engines/type-3
    7. https://www.energymanagermagazine.co.uk/hydrogen-and-combined-heat-and-power-units-chps/
    8. https://www.schmitt-enertec.com/wp-content/uploads/2017/10/RSE_FLY_CHP_2017-08_V04_EN_WEB.pdf
    9. https://www.energy.gov/sites/prod/files/2017/12/f46/CHP%20Overview-120817_compliant_0.pdf
    10. https://www.energy.gov/eere/amo/articles/gas-turbines-doe-chp-technology-fact-sheet-series-fact-sheet-2016
    11. https://assets.publishing.service.gov.uk/government/uploads/system/uploads
        /attachment_data/file/961492/Part_2_CHP_Technologies_BEIS_v03.pdf
    12. "Hydrogen-based combined heat and power systems: A review of technologies
        and challenges" by Sen Yu et. al.
    13. https://www.ge.com/content/dam/gepower-new/global/en_US/downloads/gas-new-site/
        future-of-energy/hydrogen-for-power-gen-gea34805.pdf
    14. "Comparison of District Heating Supply Options for Different CHP Configurations"
        by Pavel et. al.
    15. https://gentec.cz/wp-content/uploads/2021/09/Technical-datasheet_KE-MNG-500-BE_28.08.2023_rev1.pdf

    """

    gas_type: dict[Gas, float]
    maximum_temperature: float
    minimum_temperature: float
    input_pressure: float
    electric_efficiency: float
    thermal_efficiency: float


NATURALGAS_CHP = CHPTemplate(
    gas_type={NATURAL_GAS: 1},
    maximum_temperature=85,
    minimum_temperature=20,
    input_pressure=1,
    electric_efficiency=0.421,
    thermal_efficiency=0.454,
)

BIOGAS_CHP = CHPTemplate(
    gas_type={BIOGAS: 1},
    maximum_temperature=85,
    minimum_temperature=20,
    input_pressure=1,
    electric_efficiency=0.427,
    thermal_efficiency=0.408,
)

BIOMETHANE_CHP = CHPTemplate(
    gas_type={BIO_METHANE: 1},
    maximum_temperature=85,
    minimum_temperature=20,
    input_pressure=1,
    electric_efficiency=0.427,
    thermal_efficiency=0.46,
)

HYDROGEN_CHP = CHPTemplate(
    gas_type={HYDROGEN: 1},
    maximum_temperature=90,
    minimum_temperature=20,
    input_pressure=1,
    electric_efficiency=0.39,
    thermal_efficiency=0.474,
)

HYDROGEN_MIXED_CHP = CHPTemplate(
    gas_type={NATURAL_GAS: 0.8, HYDROGEN: 0.2},
    maximum_temperature=85,
    minimum_temperature=20,
    input_pressure=1,
    electric_efficiency=0.363,
    thermal_efficiency=0.557,
)


class CHP(AbstractTechnology, AbstractSolphRepresentation):
    """
    Combined heat and power (CHP) technology, also known as cogeneration,
    produces electricity and heat on-site. CHP systems increase energy
    security by producing energy at the point of use, and significantly
    improve energy efficiency. Depending on design, they can typically,
    accepts different types of gas or gas-mixtures as fuel input. The
    alternator connected to the gas engine, reciprocating engine or steam
    generator (boiler) produces electricity. For heat recovery, usually,
    the cooling water circuits of the engine are first linked to a plate
    heat exchanger which facilitates the transfer of hot water to an external
    hot-water circuit, typically on a 90°C/70°C flow/return basis. Any excess
    heat should be dumped using adjacent heat dump radiators to facilitate
    the correct operation of the engine. Heat extracted from CHP could be
    utilized for various applications, including, hot water, space heating,
    industrial processes, etc.

    Note: User can select one of the default CHP technology template
    (NATURALGAS_CHP, BIOGAS_CHP, BIOMETHANE_CHP, HYDROGEN_CHP, HYDROGEN_MIXED_CHP).
    These CHPs are distinguished with gas input fuel with shares in vol %, thermal
    temperature, electrical efficiency, and thermal efficiency. User can either
    change these parameters for any specific technology type or can create user-
    -defined technology if needed. Moreover, by default, HYDROGEN_MIXED_CHP type
    takes fuel input of natural gas (80 vol%) and  hydrogen (20 vol%).

    """

    @enable_templating(CHPTemplate)
    def __init__(
        self,
        name: str,
        gas_type: dict[Gas, float],
        maximum_temperature: float,
        minimum_temperature: float,
        nominal_power: float,
        input_pressure: float,
        electric_efficiency: float,
        thermal_efficiency: float,
    ):
        """
        Initialize CHP component.

        :param name: Set the name of the component
        :param gas_type: (Dict) type of gas from gas carrier and its share in
                         vol %
        :parma maximum_temperature: Maximum temperature level (in °C) of the heat output
                                    from CHP that is recoverable.
        :param minimum_temperature: Minimum return temperature level (in °C)
        :param nominal_power: Nominal electric output capacity of the CHP (in Watts)
        :param input_pressure: Input pressure of gas or gases (in bar).
        :param electric_efficiency: Electric conversion efficiency (LHV) of the CHP
        :param thermal_efficiency: Thermal conversion efficiency (LHV) of the CHP

        """
        super().__init__(name=name)

        self.gas_type = gas_type
        self.maximum_temperature = maximum_temperature
        self.minimum_temperature = minimum_temperature
        self.nominal_power = nominal_power
        self.input_pressure = input_pressure
        self.electric_efficiency = electric_efficiency
        self.thermal_efficiency = thermal_efficiency

    def build_core(self):
        """Build core structure of oemof.solph representation."""

        # Convert volume (vol% )fraction into mass fraction (%) as unit of gases
        # in MTRESS are considered in mass (kg).
        # W(i) = Vol. fraction (i) * molar_mass(i)/ ∑(Vol. fraction (i) * molar_mass(i))
        # Calculate the denominator first
        denominator = sum(
            vol_fraction * gas.molar_mass for gas, vol_fraction in self.gas_type.items()
        )
        # Convert volume fractions to mass fractions in the gas_type dictionary
        self.gas_type = {
            gas: (vol_fraction * gas.molar_mass) / denominator
            for gas, vol_fraction in self.gas_type.items()
        }

        gas_bus = {}  # gas bus for each gas type
        gas_LHV = 0  # Calculate LHV of gas or gas-mixtures

        for gas, share in self.gas_type.items():
            gas_carrier = self.location.get_carrier(GasCarrier)
            _, pressure_level = gas_carrier.get_surrounding_levels(
                gas, self.input_pressure
            )
            gas_bus[gas] = gas_carrier.distribution[gas][pressure_level]

            # Calculate LHV of gas or gas-mixture
            gas_LHV += gas.LHV * share

        # convert gas in kg to heat in Wh with thermal efficiency conversion
        heat_output = self.thermal_efficiency * gas_LHV
        heat_carrier = self.location.get_carrier(HeatCarrier)
        heat_bus_warm, heat_bus_cold, ratio = heat_carrier.get_connection_heat_transfer(
            self.maximum_temperature,
            self.minimum_temperature,
        )
        # Add electrical connection
        electricity_carrier = self.location.get_carrier(Electricity)
        electrical_bus = electricity_carrier.distribution
        # convert gas in kg to electricity in Wh with thermal efficiency conversion
        electrical_output = self.electric_efficiency * gas_LHV
        # convert nominal electrical capacity in watts to nominal gas consumption
        # in kg
        nominal_gas_consumption = self.nominal_power / (
            self.electric_efficiency * gas_LHV
        )

        # Conversion factors of the oemof converter
        conversion = {gas_bus[gas]: share for gas, share in self.gas_type.items()}
        conversion.update(
            {
                heat_bus_warm: heat_output / (1 - ratio),
                heat_bus_cold: heat_output * ratio / (1 - ratio),
                electrical_bus: electrical_output,
            }
        )

        inputs = {
            gas_bus[gas]: Flow(nominal_value=nominal_gas_consumption)
            for gas, share in self.gas_type.items()
        }
        inputs.update({heat_bus_cold: Flow()})

        self.create_solph_node(
            label="converter",
            node_type=Converter,
            inputs=inputs,
            outputs={
                electrical_bus: Flow(),
                heat_bus_warm: Flow(),
            },
            conversion_factors=conversion,
        )
