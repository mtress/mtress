"""This module provides hydrogen compressors."""

from oemof.solph import Bus, Flow
from oemof.solph.components import Converter

from .._abstract_component import AbstractSolphRepresentation
from ..carriers import Electricity, Hydrogen, Gas
from ..physics import calc_isothermal_compression_energy
from ._abstract_technology import AbstractTechnology


class GasCompressor(AbstractTechnology, AbstractSolphRepresentation):
    """Ideal gas compressor."""

    def __init__(
            self,
            name: str,
            nominal_power: float,
            gas_const: float = 518.28,
            unit_conversion: float = 11.2,
            isothermal_efficiency: float = 0.85,
    ):
        """
        Initialize gas compressor.

        :param name: Name of the component
        :param nominal_power: Nominal power
        :param gas_const: gas const, default to 518.28 for NG.
        :param unit_conversion: Calorific value if gases is given in kWh,
                                default to 11.2 KWh/kg for NG. If gases is
                                in kg, unit_conversion must be 1.
        :param isothermal_efficiency: Isothermal efficiency, defaults to .85
        """
        super().__init__(name=name)

        self.nominal_power = nominal_power
        self.gas_const = gas_const
        self.unit_conversion = unit_conversion
        self.isothermal_efficiency = isothermal_efficiency

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        gas_carrier = self.location.get_carrier(Gas)
        electricity_carrier = self.location.get_carrier(Electricity)

        electrical_input = self.create_solph_node(
            label="electrical_input",
            node_type=Bus,
            inputs={
                electricity_carrier.distribution: Flow(nominal_value=self.nominal_power)
            },
        )

        pressure_low = None

        for pressure in gas_carrier.pressure_levels:
            if pressure_low is not None:
                self.create_solph_node(
                    label=f"compress_{pressure_low:.0f}_{pressure:.0f}",
                    node_type=Converter,
                    inputs={
                        electrical_input: Flow(),
                        gas_carrier.outputs[pressure_low]: Flow(),
                    },
                    outputs={gas_carrier.outputs[pressure]: Flow()},
                    conversion_factors={
                        gas_carrier.outputs[pressure_low]: 1,
                        gas_carrier.outputs[pressure]: 1,
                        electrical_input: (
                                calc_isothermal_compression_energy(pressure_low, pressure,
                                                                   R=self.gas_const,
                                                                   unit_conversion=self.unit_conversion)
                                / self.isothermal_efficiency
                        ),
                    },
                )

            pressure_low = pressure
