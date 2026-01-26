"""This module provides hydrogen compressors."""

from oemof.solph import Bus, Flow, Investment
from oemof.solph.components import Converter

from ..carriers import ElectricityCarrier, GasCarrier
from ..physics import (
    IDEAL_GAS_CONSTANT,
    Gas,
    calc_isothermal_compression_energy,
)
from ._abstract_technology import AbstractTechnology

from .._constants import EnergyType


class GasCompressor(AbstractTechnology):
    """Ideal gas compressor."""

    def __init__(
        self,
        name: str,
        nominal_power: Investment | float,
        gas_type: Gas,
        isothermal_efficiency: float = 0.85,
    ):
        """
        Initialize gas compressor.

        :param name: Name of the compressor component
        :param nominal_power: Nominal power (in W)
        :param gas_type: Type of gas, for ex. HYDROGEN, NATURAL_GAS, etc.
        :param isothermal_efficiency: Isothermal efficiency, defaults to .85
        """
        super().__init__(name=name)

        self.nominal_power = nominal_power
        self.isothermal_efficiency = isothermal_efficiency
        self.gas_type = gas_type

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        super().build_core()

        gas_carrier = self.location.get_carrier(GasCarrier)
        electricity_carrier = self.location.get_carrier(ElectricityCarrier)

        electrical_input = self.create_solph_node(
            label="electrical_input",
            node_type=Bus,
            inputs={
                electricity_carrier.distribution: Flow(
                    custom_properties={
                        "unit": "W",
                        "energy_type": EnergyType.ELECTRICITY,
                    },
                    nominal_value=self.nominal_power,
                )
            },
        )

        pressure_low = None
        for pressure in gas_carrier.pressure_levels[self.gas_type]:
            if pressure_low is not None:
                self.create_solph_node(
                    label=f"compress_{pressure_low}_{pressure}",
                    node_type=Converter,
                    inputs={
                        electrical_input: Flow(
                            custom_properties={
                                "unit": "W",
                                "energy_type": EnergyType.ELECTRICITY,
                            }
                        ),
                        gas_carrier.outputs[self.gas_type][pressure_low]: Flow(
                            custom_properties={
                                "unit": "kg/h",
                                "energy_type": EnergyType.GAS,
                            }
                        ),
                    },
                    outputs={
                        gas_carrier.outputs[self.gas_type][pressure]: Flow(
                            custom_properties={
                                "unit": "kg/h",
                                "energy_type": EnergyType.GAS,
                            }
                        )
                    },
                    conversion_factors={
                        gas_carrier.outputs[self.gas_type][pressure_low]: 1,
                        gas_carrier.outputs[self.gas_type][pressure]: 1,
                        electrical_input: (
                            calc_isothermal_compression_energy(
                                pressure_low,
                                pressure,
                                R=IDEAL_GAS_CONSTANT
                                / self.gas_type.molar_mass,
                            )
                            / self.isothermal_efficiency
                        ),
                    },
                )

            pressure_low = pressure
