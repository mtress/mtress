# -*- coding: utf-8 -*-

"""
Abstract heat storage with undefined internal reperesentation.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

SPDX-License-Identifier: MIT
"""

from mtress._abstract_component import AbstractSolphComponent
from mtress._data_handler import TimeseriesSpecifier

from .._abstract_technology import AbstractTechnology


class AbstractHeatStorage(AbstractTechnology, AbstractSolphComponent):
    """
    Base class and interface for heat storage technologies.
    """

    def __init__(
        self,
        name: str,
        diameter: float,
        volume: float,
        ambient_temperature: TimeseriesSpecifier,
        u_value: float | None = None,
    ):
        """
        Create layered heat storage component.

        :param diameter: Diameter of the storage in m
        :param volume: Volume of the storage in m³
        :param u_value: Thermal transmittance in W/m²/K
        :param ambient_temperature: Ambient temperature in deg C
        """
        super().__init__(name)

        # General parameters of the storage
        self.diameter = diameter
        self.volume = volume
        self.ambient_temperature = ambient_temperature
        if u_value is None or u_value > 0:
            self.u_value = u_value
        else:
            raise ValueError("u_value needs to be positive.")
