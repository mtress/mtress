"""This module provides hydrogen compressors."""

from oemof import solph

from ..carriers import Hydrogen
from ..physics import calc_isothermal_compression_energy
from ._abstract_technology import AbstractTechnology


class H2Compressor(AbstractTechnology):
    """Ideal gas compressor."""

    def __init__(
        self, nominal_power: float, isothermal_efficiency: float = 0.85, **kwargs
    ):
        """
        Initialize air heat exchanger for e.g. heat pumps.

        :param nominal_power: Nominal power of the heat exchanger.
        :param isothermal_efficiency: Isothermal efficiency of the compressor
        """
        super().__init__(**kwargs)

        self._nominal_power = nominal_power

        h2_carrier = self.location.get_carrier(Hydrogen)
        electrical_bus = solph.Bus(label=self._generate_label("electrical_bus"))

        self.location.energy_system.add(electrical_bus)

        pressure_low = None
        for pressure in h2_carrier.pressure_levels:
            if pressure_low is not None:
                compressor = solph.Transformer(
                    label=self._generate_label(
                        f"compress_{pressure_low:.0f}_{pressure:.0f}"
                    ),
                    inputs={
                        electrical_bus: solph.Flow(),
                        h2_carrier.outputs[pressure_low]: solph.Flow(),
                    },
                    outputs={h2_carrier.outputs[pressure]: solph.Flow()},
                    conversion_factors={
                        h2_carrier.outputs[pressure_low]: 1,
                        h2_carrier.outputs[pressure]: 1,
                        electrical_bus: (
                            calc_isothermal_compression_energy(pressure_low, pressure)
                            / isothermal_efficiency
                        ),
                    },
                )

                self.location.energy_system.add(compressor)

            pressure_low = pressure

        source = solph.Bus(label=self._generate_label("source"))
        self._bus = bus = solph.Bus(
            label=self._generate_label("output"),
            inputs={source: solph.Flow(nominal_value=nominal_power)},
        )

        self.location.energy_system.add(source, bus)
