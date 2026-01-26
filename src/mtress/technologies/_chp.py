"""This module provides combined heat and power (CHP)"""

import logging
from dataclasses import dataclass
import warnings

from oemof.solph import Flow, Bus, NonConvex, Investment
from oemof.solph.components import (
    Converter,
    OffsetConverter,
    slope_offset_from_nonconvex_input,
)

from .._helpers._util import enable_templating
from ..carriers import ElectricityCarrier, GasCarrier
from ..physics import BIO_METHANE, BIOGAS, HYDROGEN, NATURAL_GAS, Gas
from ._heater import AbstractHeater

from .._constants import EnergyType

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
    12. "Hydrogen-based combined heat and power systems: A review of
        technologies and challenges" by Sen Yu et. al.
    13. https://www.ge.com/content/dam/gepower-new/global/en_US/downloads/gas-new-site/
        future-of-energy/hydrogen-for-power-gen-gea34805.pdf
    14. "Comparison of District Heating Supply Options for Different
        CHP Configurations" by Pavel et. al.
    15. https://gentec.cz/wp-content/uploads/2021/09/Technical-datasheet_KE-MNG-500-BE_28.08.2023_rev1.pdf

    """

    gas_type: dict[Gas, float]
    maximum_temperature: float
    minimum_temperature: float
    input_pressure: float
    nominal_electrical_efficiency: float
    nominal_thermal_efficiency: float
    min_load_electrical_efficiency: float
    min_load_thermal_efficiency: float
    normalised_min_load: float
    nominal_power: float


NATURALGAS_CHP = CHPTemplate(
    gas_type={NATURAL_GAS: 1},
    maximum_temperature=85,
    minimum_temperature=20,
    input_pressure=1,
    nominal_electrical_efficiency=0.421,
    nominal_thermal_efficiency=0.454,
    min_load_electrical_efficiency=0.421,
    min_load_thermal_efficiency=0.454,
    normalised_min_load=0.1,
    nominal_power=500e3,  # W (electrical)
)

BIOGAS_CHP = CHPTemplate(
    gas_type={BIOGAS: 1},
    maximum_temperature=85,
    minimum_temperature=20,
    input_pressure=1,
    nominal_electrical_efficiency=0.427,
    nominal_thermal_efficiency=0.408,
    min_load_electrical_efficiency=0.427,
    min_load_thermal_efficiency=0.408,
    normalised_min_load=0.1,
    nominal_power=500e3,  # W (electrical)
)

BIOMETHANE_CHP = CHPTemplate(
    gas_type={BIO_METHANE: 1},
    maximum_temperature=85,
    minimum_temperature=20,
    input_pressure=1,
    nominal_electrical_efficiency=0.427,
    nominal_thermal_efficiency=0.46,
    min_load_electrical_efficiency=0.427,
    min_load_thermal_efficiency=0.46,
    normalised_min_load=0.1,
    nominal_power=500e3,  # W (electrical)
)

HYDROGEN_CHP = CHPTemplate(
    gas_type={HYDROGEN: 1},
    maximum_temperature=90,
    minimum_temperature=20,
    input_pressure=1,
    nominal_electrical_efficiency=0.39,
    nominal_thermal_efficiency=0.474,
    min_load_electrical_efficiency=0.39,
    min_load_thermal_efficiency=0.474,
    normalised_min_load=0.1,
    nominal_power=500e3,  # W (electrical)
)

HYDROGEN_MIXED_CHP = CHPTemplate(
    gas_type={NATURAL_GAS: 0.8, HYDROGEN: 0.2},
    maximum_temperature=85,
    minimum_temperature=20,
    input_pressure=1,
    nominal_electrical_efficiency=0.363,
    nominal_thermal_efficiency=0.557,
    min_load_electrical_efficiency=0.363,
    min_load_thermal_efficiency=0.557,
    normalised_min_load=0.1,
    nominal_power=500e3,  # W (electrical)
)

# Ansaldo Energia's T100 MGT
# source: https://www.ansaldoenergia.com/offering/equipment/turbomachinery/microturbines/ae-t-100
# i.e.: https://www.ansaldoenergia.com/fileadmin/Brochure/AnsaldoEnergia-Microturbine-AE-T100NG-20220907.pdf
NATURALGAS_MGT = CHPTemplate(
    gas_type={NATURAL_GAS: 1},
    maximum_temperature=110,  # Celsius (LUT data)
    minimum_temperature=20,  # Celsius (LUT data)
    input_pressure=0.1,  # 0.02-0.1 bar
    nominal_electrical_efficiency=0.295,  # average @ nom. load
    nominal_thermal_efficiency=0.500,  # average @ nom. load
    min_load_electrical_efficiency=0.239,  # average @ min. load
    min_load_thermal_efficiency=0.490,  # average @ min. load
    normalised_min_load=0.45,
    nominal_power=100e3,  # W (electrical)
)


class CHP(AbstractHeater):
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
    (NATURALGAS_CHP, BIOGAS_CHP, BIOMETHANE_CHP, HYDROGEN_CHP,
    HYDROGEN_MIXED_CHP).
    These CHPs are distinguished with gas input fuel with shares in vol %,
    thermal temperature, electrical efficiency, and thermal efficiency.
    User can either change these parameters for any specific technology type or
    can create user-defined technology if needed. Moreover, by default,
    HYDROGEN_MIXED_CHP type takes fuel input of natural gas (80 vol%) and
    hydrogen (20 vol%).
    """

    @enable_templating(CHPTemplate)
    def __init__(
        self,
        name: str,
        gas_type: dict[Gas, float],
        maximum_temperature: float,
        minimum_temperature: float,
        nominal_power: float | Investment,
        input_pressure: float,
        nominal_electrical_efficiency: float,
        nominal_thermal_efficiency: float,
        allow_electricity_feed_in: bool = True,
    ):
        """
        Initialize CHP component.

        :param name: Set the name of the component
        :param gas_type: (Dict) type of gas from gas carrier and its share in
                         vol %
        :parma maximum_temperature: Maximum temperature level (in °C) of the
            heat output from CHP that is recoverable.
        :param minimum_temperature: Minimum return temperature level (in °C)
        :param nominal_power: Nominal electric output capacity of the CHP
            (in Watts)
        :param input_pressure: Input pressure of gas or gases (in bar).
        :param nominal_electrical_efficiency: Electric conversion efficiency
            (LHV) of the CHP
        :param nominal_thermal_efficiency: Thermal conversion efficiency
            (LHV) of the CHP

        """
        super().__init__(
            name=name,
            maximum_temperature=maximum_temperature,
            minimum_temperature=minimum_temperature,
        )

        self.gas_type = gas_type
        self.nominal_power = nominal_power
        self.input_pressure = input_pressure
        self.nominal_electrical_efficiency = nominal_electrical_efficiency
        self.nominal_thermal_efficiency = nominal_thermal_efficiency
        self.allow_electricity_feed_in = allow_electricity_feed_in

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        # Convert volume (vol% )fraction into mass fraction (%) as unit
        # of gases in MTRESS are considered in mass (kg).
        # W(i) =
        # Vol. fraction(i) * molar_mass(i)/ ∑(Vol. fraction(i) * molar_mass(i))
        # Calculate the denominator first
        denominator = sum(
            vol_fraction * gas.molar_mass
            for gas, vol_fraction in self.gas_type.items()
        )
        # Convert volume fractions to mass fractions in the gas_type dictionary
        # self.gas_type = {
        #     gas: (vol_fraction * gas.molar_mass) / denominator
        #     for gas, vol_fraction in self.gas_type.items()
        # }
        mass_fractions = {
            gas: (vol_fraction * gas.molar_mass) / denominator
            for gas, vol_fraction in self.gas_type.items()
        }

        # *********************************************************************
        # *********************************************************************

        # Add gas connections
        gas_buses = {}  # gas bus for each gas type
        for gas, mass_fraction in mass_fractions.items():
            # gas bus
            gas_carrier = self.location.get_carrier(GasCarrier)
            _, pressure_level = gas_carrier.get_surrounding_levels(
                gas, self.input_pressure
            )
            gas_buses[gas] = gas_carrier.distribution[gas][pressure_level]

        # Add electrical connection
        electricity_carrier = self.location.get_carrier(ElectricityCarrier)

        # Add heat connection? probably done in super().build_core()
        # self.heat_bus

        # *********************************************************************
        # *********************************************************************

        gas_mix_LHV = sum(
            gas.LHV * mass_fraction
            for gas, mass_fraction in mass_fractions.items()
        )

        # Electrical efficiency with conversion from gas in kg
        # to electricity in W
        gas_to_elec_cf = self.nominal_electrical_efficiency * gas_mix_LHV

        # thermal efficiency with conversion from gas in kg to heat in W.
        gas_to_heat_cf = self.nominal_thermal_efficiency * gas_mix_LHV

        # *********************************************************************
        # *********************************************************************

        if self.allow_electricity_feed_in:

            splitter = self.create_solph_node(
                label="splitter",
                node_type=Bus,
                outputs={
                    electricity_carrier.feed_in: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.ELECTRICITY,
                        }
                    ),
                    electricity_carrier.distribution: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.ELECTRICITY,
                        }
                    ),
                },
            )

            # entry node: gases come in, gas mix goes out
            gas_mixer_bus = self.create_solph_node(
                label="mixer",
                node_type=Bus,
                inputs={
                    gas_bus: Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.GAS,
                        }
                    )
                    for gas, gas_bus in gas_buses.items()
                },
            )

            # final node: gas mix goes in, heat and electricity come out
            self.create_solph_node(
                label="CHP",
                node_type=Converter,
                inputs={
                    gas_mixer_bus: Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.GAS,
                        },
                    )
                },
                outputs={
                    self.heat_bus: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.HEAT,
                        }
                    ),
                    splitter: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.ELECTRICITY,
                        },
                        nominal_value=self.nominal_power,
                    ),
                },
                conversion_factors={
                    gas_mixer_bus: 1,
                    self.heat_bus: gas_to_heat_cf,
                    splitter: gas_to_elec_cf,
                },
            )
        else:

            # entry node: gases come in, gas mix goes out
            gas_mixer_bus = self.create_solph_node(
                label="mixer",
                node_type=Bus,
                inputs={
                    gas_bus: Flow(custom_properties={"unit": "kg/h"})
                    for gas, gas_bus in gas_buses.items()
                },
            )

            # final node: gas mix goes in, heat and electricity come out
            self.create_solph_node(
                label="CHP",
                node_type=Converter,
                inputs={
                    gas_mixer_bus: Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.GAS,
                        },
                    )
                },
                outputs={
                    self.heat_bus: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.HEAT,
                        }
                    ),
                    electricity_carrier.distribution: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.ELECTRICITY,
                        },
                        nominal_value=self.nominal_power,
                    ),
                },
                conversion_factors={
                    gas_mixer_bus: 1,
                    self.heat_bus: gas_to_heat_cf,
                    electricity_carrier.distribution: gas_to_elec_cf,
                },
            )


class OffsetCHP(AbstractHeater):
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

    This class allows users to characterise the nominal and part-load
    performance of a CHP unit using two setpoints. The performance variation
    between these two setpoints is assumed to be linear. If the maximum load is
    expected to exceed the nominal capacity (normalised_max_load >= 1) the
    efficiency values will be extrapolated based on the linear curves.

    """

    @enable_templating(CHPTemplate)
    def __init__(
        self,
        name: str,
        gas_type: dict[Gas, float],
        maximum_temperature: float,
        minimum_temperature: float,
        nominal_power: Investment | float,
        input_pressure: float,
        nominal_electrical_efficiency: float,
        nominal_thermal_efficiency: float,
        min_load_electrical_efficiency: float,
        min_load_thermal_efficiency: float,
        normalised_min_load: float,
        normalised_max_load: float = 1,
        allow_electricity_feed_in: bool = True,
    ):
        """ """
        super().__init__(
            name=name,
            maximum_temperature=maximum_temperature,
            minimum_temperature=minimum_temperature,
        )

        self.gas_type = gas_type
        self.nominal_power = nominal_power
        self.input_pressure = input_pressure
        self.nominal_electrical_efficiency = nominal_electrical_efficiency
        self.nominal_thermal_efficiency = nominal_thermal_efficiency
        self.min_load_electrical_efficiency = min_load_electrical_efficiency
        self.min_load_thermal_efficiency = min_load_thermal_efficiency
        self.normalised_min_load = normalised_min_load
        self.normalised_max_load = normalised_max_load
        self.allow_electricity_feed_in = allow_electricity_feed_in

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        # Convert volume (vol% )fraction into mass fraction (%) as unit
        # of gases in MTRESS are considered in mass (kg).
        # W(i) =
        # Vol. fraction(i) * molar_mass(i)/ ∑(Vol. fraction(i) * molar_mass(i))
        # Calculate the denominator first
        denominator = sum(
            vol_fraction * gas.molar_mass
            for gas, vol_fraction in self.gas_type.items()
        )
        # Convert volume fractions to mass fractions in the gas_type dictionary
        mass_fractions = {
            gas: (vol_fraction * gas.molar_mass) / denominator
            for gas, vol_fraction in self.gas_type.items()
        }

        # *********************************************************************
        # *********************************************************************

        # Add gas connections
        gas_buses = {}  # gas bus for each gas type
        for gas, _ in mass_fractions.items():
            # gas bus
            gas_carrier = self.location.get_carrier(GasCarrier)
            _, pressure_level = gas_carrier.get_surrounding_levels(
                gas, self.input_pressure
            )
            gas_buses[gas] = gas_carrier.distribution[gas][pressure_level]

        # Add electrical connection
        electricity_carrier = self.location.get_carrier(ElectricityCarrier)

        # Add heat connection? probably done in super().build_core()
        # self.heat_bus

        # *********************************************************************
        # *********************************************************************

        gas_mix_LHV = sum(
            gas.LHV * mass_fraction
            for gas, mass_fraction in mass_fractions.items()
        )

        # Gas input with conversion from electricity to gas in kg
        nominal_fuel_input = 1 / (self.nominal_electrical_efficiency *
                                  gas_mix_LHV)

        # thermal efficiency with conversion from electricity to gas in kg to
        # heat in W.
        nominal_heat_output = ((self.nominal_thermal_efficiency * gas_mix_LHV)
                               * nominal_fuel_input)

        min_load_fuel_input = 1 / (self.min_load_electrical_efficiency *
                                   gas_mix_LHV)

        min_load_heat_output = ((self.min_load_thermal_efficiency *
                                 gas_mix_LHV) * nominal_fuel_input)

        if self.allow_electricity_feed_in:
            splitter_bus = self.create_solph_node(
                label="splitter",
                node_type=Bus,
                outputs={
                    electricity_carrier.feed_in: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.ELECTRICITY,
                        }
                    ),
                    electricity_carrier.distribution: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.ELECTRICITY,
                        }
                    ),
                },
            )

            # entry node: gases come in, gas mix goes out
            gas_mixer_bus = self.create_solph_node(
                label="mixer",
                node_type=Bus,
                inputs={
                    gas_bus: Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.GAS,
                        }
                    )
                    for _, gas_bus in gas_buses.items()
                },
            )

            # final node: gas mix goes in, heat and electricity come out

            # offset mode
            slope_fl, offset_fl = slope_offset_from_nonconvex_input(
                self.normalised_max_load,
                self.normalised_min_load,
                nominal_fuel_input,
                min_load_fuel_input,
            )

            slope_ht, offset_ht = slope_offset_from_nonconvex_input(
                self.normalised_max_load,
                self.normalised_min_load,
                nominal_heat_output,
                min_load_heat_output,
            )

            self.create_solph_node(
                label="CHP",
                node_type=OffsetConverter,
                inputs={
                    gas_mixer_bus: Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.GAS,
                        },
                    ),
                },

                outputs={
                    splitter_bus: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.ELECTRICITY,
                        },
                        nominal_value=self.nominal_power,
                        max=self.normalised_max_load,
                        min=self.normalised_min_load,
                        nonconvex=NonConvex(),

                    ),
                    self.heat_bus: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.HEAT,
                        }
                    ),
                },
                conversion_factors={
                    gas_mixer_bus: slope_fl,
                    self.heat_bus: slope_ht,
                },
                normed_offsets={
                    gas_mixer_bus: offset_fl,
                    self.heat_bus: offset_ht,
                },
            )

        else:

            # entry node: gases come in, gas mix goes out
            gas_mixer_bus = self.create_solph_node(
                label="mixer",
                node_type=Bus,
                inputs={
                    gas_bus: Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.GAS,
                        }
                    )
                    for gas, gas_bus in gas_buses.items()
                },
            )

            # final node: gas mix goes in, heat and electricity come out

            # offset mode
            slope_fl, offset_fl = slope_offset_from_nonconvex_input(
                self.normalised_max_load,
                self.normalised_min_load,
                nominal_fuel_input,
                min_load_fuel_input,
            )

            slope_ht, offset_ht = slope_offset_from_nonconvex_input(
                self.normalised_max_load,
                self.normalised_min_load,
                nominal_heat_output,
                min_load_heat_output,
            )

            self.create_solph_node(
                label="CHP",
                node_type=OffsetConverter,
                inputs={
                    gas_mixer_bus: Flow(
                        custom_properties={
                            "unit": "kg/h",
                            "energy_type": EnergyType.GAS,
                        },
                    ),
                },
                outputs={
                    electricity_carrier.distribution: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.ELECTRICITY,
                        },
                        nominal_value=self.nominal_power,
                        max=self.normalised_max_load,
                        min=self.normalised_min_load,
                        nonconvex=NonConvex(),
                    ),
                    self.heat_bus: Flow(
                        custom_properties={
                            "unit": "W",
                            "energy_type": EnergyType.HEAT,
                        }
                    ),
                },
                conversion_factors={
                    gas_mixer_bus: slope_fl,
                    self.heat_bus: slope_ht,
                },
                normed_offsets={
                    gas_mixer_bus: offset_fl,
                    self.heat_bus: offset_ht,
                },
            )
