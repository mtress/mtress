"""
Storage that has a homogeneous pressure distribution.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

SPDX-License-Identifier: MIT
"""
from mtress.carriers import HYDROGEN
from mtress.physics import calc_hydrogen_density

from .._mixed_gas_storage import Implementation
from ._abstract_gas_storage import AbstractGasStorage


class H2Storage(AbstractGasStorage):
    """
    Fully mixed hydrogen storage.

    Fully mixed hydrogen storage that ensures access only when suitable input_pressure levels
    are reached.
    """

    def __init__(
        self,
        name: str,
        volume: float,
        power_limit: float,
        multiplexer_implementation: Implementation | str = Implementation.STRICT,
    ):
        """
        Create fully mixed hydrogen storage component.

        :param name: Name of the component
        :param volume: Volume of the storage in m³
        :param power_limit: Power limit in kW
        """
        if not isinstance(multiplexer_implementation, Implementation):
            multiplexer_implementation = Implementation(multiplexer_implementation)

        super().__init__(
            name=name,
            volume=volume,
            power_limit=power_limit,
            implementation=multiplexer_implementation,
            calc_density=calc_hydrogen_density,
        )

    def build_core(self) -> None:
        """Build the core structure of mtress representation."""
        self.build_storage(gas_type=HYDROGEN)
