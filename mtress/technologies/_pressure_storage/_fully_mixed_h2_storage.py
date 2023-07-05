"""
Storage that has a homogeneous pressure distribution.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

SPDX-License-Identifier: MIT
"""
from mtress._data_handler import TimeseriesSpecifier
from mtress.carriers import Hydrogen
from mtress.physics import bar_to_pascal, HYDROGEN_MOLAR_MASS, IDEAL_GAS_CONSTANT
from .._mixed_storage import AbstractMixedStorage, Implementation
from ._abstract_pressure_storage import AbstractPressureStorage


def get_hydrogen_density(pressure: float = 1, temperature: float = 25) -> float:
    """
    Calculate the density of hydrogen gas.
    :param temperature: H2 gas temperature in the storage tank
    :param pressure: Pressure of hydrogen gas (in bar)
    :return: Density of hydrogen gas (in kilograms per cubic meter)
    """
    # Conversion factors
    pressure_pascal = pressure * 100000

    gas_temperature = 273 + temperature

    # Calculate density (kg/Nm3/bar) using ideal gas equation under 1 bar pressure
    density = (pressure_pascal * HYDROGEN_MOLAR_MASS) / (IDEAL_GAS_CONSTANT * gas_temperature)

    return density


class FullyMixedH2Storage(AbstractMixedStorage, AbstractPressureStorage):
    """
    Fully mixed hydrogen storage.

    Fully mixed hydrogen storage that ensures access only when suitable pressure levels are reached.
    """

    def __init__(
            self,
            name: str,
            diameter: float,
            volume: float,
            power_limit: float,
            u_value: float | None = None,
            multiplexer_implementation: Implementation | str = Implementation.STRICT,
            compressibility_factor: float = 1.0):

        """
        Create fully mixed hydrogen storage component.

        :param name: Name of the component
        :param diameter: Diameter of the storage in m
        :param volume: Volume of the storage in m³
        :param power_limit: Power limit in kW
        :param u_value: Thermal transmittance in W/m²/K
        """
        if not isinstance(multiplexer_implementation, Implementation):
            multiplexer_implementation = Implementation(multiplexer_implementation)

        super().__init__(
            name=name,
            diameter=diameter,
            volume=volume,
            power_limit=power_limit,
            u_value=u_value,
            implementation=multiplexer_implementation,
            compressibility_factor=compressibility_factor,
        )

    def build_core(self):
        """Build the core structure of mtress representation."""
        carrier: Hydrogen = self.location.get_carrier(Hydrogen)
        hydrogen_density = get_hydrogen_density()
        capacity_per_unit = (self.volume * hydrogen_density)/self.compressibility_factor
        empty_level = 0

        solph_storage_arguments = {
            "nominal_storage_capacity": (max(carrier.pressure_levels) - empty_level
                                         ) * capacity_per_unit
        }

        if self.u_value is None:
            solph_storage_arguments.update(
                {
                    "loss_rate": 0,
                    "fixed_losses_relative": 0,
                    "fixed_losses_absolute": 0,
                }
            )
        else:
            raise NotImplementedError(
                "u_value is not implemented for this kind of storage"
            )

        self.build_multiplexer_structure(
            carrier,
            capacity_per_unit,
            self.power_limit,
            empty_level,
            solph_storage_arguments,
        )
