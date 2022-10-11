"""This module provides hydrogen electrolysers."""

import logging

import numpy as np
from oemof import solph

from ..carriers import Electricity, Heat, Hydrogen
from ..physics import H2_HHV
from ._abstract_technology import AbstractTechnology

LOGGER = logging.getLogger(__file__)


class PEMElectrolyzer(AbstractTechnology):
    """PEM electrolyzer."""

    def __init__(
        self,
        nominal_power: float,
        hydrogen_efficiency: float = 0.7,
        thermal_efficiency: float = 0.2,
        waste_heat_temperature: float = 75.0,
        hydrogen_output_pressure: float = 30.0,
        minimal_power: float = 0.2,
        **kwargs,
    ):
        """
        Initialize PEM electrolyser.

        :param nominal_power: Nominal electrical power of the component
        :param hydrogen_efficiency: Electrical efficiency of the electrolyzer,
            i.e. ratio of heat output and electrical input
        :param thermal_efficiency: Thermal efficiency of the electrolyzer,
            i.e. ratio of thermal output and electrical input
        :param minimal_power: Minimal power relative to nominal power, defaults to 0.2
        """
        super().__init__(**kwargs)

        self._nominal_power = nominal_power
        self._minimal_power = minimal_power

        # Electrical connection
        electricity_carrier = self.location.get_carrier(Electricity)
        electrical_bus = electricity_carrier.distribution

        # Hydrogen connection
        h2_carrier = self.location.get_carrier(Hydrogen)

        # PEM electrolyzers produce hydrogen at a pressure of around 30 bar, see e.g.
        # https://en.wikipedia.org/wiki/Polymer_electrolyte_membrane_electrolysis
        # or https://www.h-tec.com/produkte/detail/h-tec-pem-elektrolyseur-me450/me450/
        pressure_low, _ = h2_carrier.get_surrounding_levels(
            hydrogen_output_pressure
        )
        assert not np.isinf(
            pressure_low
        ), "No suitable pressure level available"

        h2_bus = h2_carrier.inputs[pressure_low]

        # Calculate H2 output in kg
        h2_output = hydrogen_efficiency / H2_HHV

        # Heat connection
        heat_carrier = self.location.get_carrier(Heat)

        # PEM electrolyzers produce waste heat at arrount 77 °C
        # see e.g. Heat Management of PEM Electrolysis. A study on the potential of
        # excess heat from medium­ to large­scale PEM electrolyisis and the performance
        # analysis of a dedicated cooling system by W.J. Tiktak
        temp_level, _ = heat_carrier.get_surrounding_levels(
            waste_heat_temperature
        )
        assert not np.isinf(
            temp_level
        ), "No suitable temperature level available"

        if waste_heat_temperature - temp_level > 15:
            LOGGER.info(
                "Waste heat temperature significantly"
                "higher than suitable temperature level"
            )

        heat_bus = heat_carrier.inputs[temp_level]

        # TODO: Minimal power implementieren
        transformer = solph.Transformer(
            label=self._generate_label("transformer"),
            inputs={
                electrical_bus: solph.Flow(nominal_value=self._nominal_power)
            },
            outputs={h2_bus: solph.Flow(), heat_bus: solph.Flow()},
            conversion_factors={
                electrical_bus: 1,
                h2_bus: h2_output,
                heat_bus: thermal_efficiency,
            },
        )

        self.location.energy_system.add(transformer)
