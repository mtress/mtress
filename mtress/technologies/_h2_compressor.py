"""This module provides hydrogen compressors."""

from oemof.solph import Bus, Flow
from oemof.solph.components import Transformer

from .._abstract_component import AbstractSolphComponent
from ..carriers import Electricity, Hydrogen
from ..physics import calc_isothermal_compression_energy
from ._abstract_technology import AbstractTechnology


class H2Compressor(AbstractTechnology, AbstractSolphComponent):
    """Ideal gas compressor."""

    def __init__(
        self,
        name: str,
        nominal_power: float,
        isothermal_efficiency: float = 0.85,
    ):
        """
        Initialize H2 compressor.

        :param nominal_power: Nominal power
        :param isothermal_efficiency: Isothermal efficiency, defaults to .85
        """
        super().__init__(name)

        self.nominal_power = nominal_power
        self.isothermal_efficiency = isothermal_efficiency

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        h2_carrier = self.location.get_carrier(Hydrogen)
        electricity_carrier = self.location.get_carrier(Electricity)

        electrical_bus = self.create_solph_component(
            label="electrical_bus",
            component=Bus,
            inputs={
                electricity_carrier.distribution: Flow(nominal_value=self.nominal_power)
            },
        )

        pressure_low = None
        for pressure in h2_carrier.pressure_levels:
            if pressure_low is not None:
                self.create_solph_component(
                    label=f"compress_{pressure_low:.0f}_{pressure:.0f}",
                    component=Transformer,
                    inputs={
                        electrical_bus: Flow(),
                        h2_carrier.outputs[pressure_low]: Flow(),
                    },
                    outputs={h2_carrier.outputs[pressure]: Flow()},
                    conversion_factors={
                        h2_carrier.outputs[pressure_low]: 1,
                        h2_carrier.outputs[pressure]: 1,
                        electrical_bus: (
                            calc_isothermal_compression_energy(pressure_low, pressure)
                            / self.isothermal_efficiency
                        ),
                    },
                )

            pressure_low = pressure
