"""
Storage that has a homogeneous pressure distribution.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

SPDX-License-Identifier: MIT
"""
from mtress.physics import HYDROGEN
from mtress.physics import calc_hydrogen_density

from .._abstract_homogenous_storage import Implementation
from ._gas_storage import GasStorage


class H2Storage(GasStorage):
    """
    Fully mixed hydrogen storage.

    Fully mixed hydrogen storage that ensures access only when suitable pressure levels
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
        super().__init__(
            name=name,
            gas_type=HYDROGEN,
            volume=volume,
            power_limit=power_limit,
            implementation=multiplexer_implementation,
            calc_density=calc_hydrogen_density,
        )
