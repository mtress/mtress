# -*- coding: utf-8 -*-

"""
Abstract heat storage with undefined internal reperesentation.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

SPDX-License-Identifier: MIT
"""

from mtress._abstract_component import AbstractSolphRepresentation
from mtress._data_handler import TimeseriesSpecifier

from .._abstract_technology import AbstractTechnology


class AbstractHeatStorage(AbstractTechnology, AbstractSolphRepresentation):
    """Base class and interface for heat storage technologies."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        diameter: float,
        volume: float,
        power_limit: float,
        ambient_temperature: TimeseriesSpecifier,
        u_value: float | None = None,
        max_temperature: float | None = None,
        min_temperature: float | None = None,
        **kwargs,
    ):
        """
        Create heat storage component.

        :param name: Name of the component
        :param diameter: Diameter of the storage (in m)
        :param volume: Volume of the storage (in m³)
        :param power_limit: power limit (in W)
        :param ambient_temperature: Ambient temperature (in °C)
        :param u_value: Thermal transmittance (in W/m²/K)
        """
        super().__init__(**kwargs)

        # General parameters of the storage
        self.diameter = diameter
        self.volume = volume
        self.power_limit = power_limit
        self.ambient_temperature = ambient_temperature
        self.max_temperature = max_temperature
        self.min_temperature = min_temperature

        # TODO: Why do we check the u_value but not the other parameters?
        if u_value is None or u_value > 0:
            self.u_value = u_value
        else:
            raise ValueError("u_value needs to be positive.")
