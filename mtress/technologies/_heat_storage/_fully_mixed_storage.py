# -*- coding: utf-8 -*-

"""
Storage that has a homogenious temperature distribution.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

SPDX-License-Identifier: MIT
"""
from mtress._data_handler import TimeseriesSpecifier
from mtress.carriers import Heat
from mtress.physics import H2O_DENSITY, H2O_HEAT_CAPACITY, kJ_to_MWh

from .._abstract_homogenous_storage import AbstractHomogenousStorage, Implementation
from ._abstract_heat_storage import AbstractHeatStorage


class FullyMixedHeatStorage(AbstractHeatStorage, AbstractHomogenousStorage):
    """
    Fully mixed heat storage.

    Fully mixed heat storage that makes sure access is only when temperatures
    are suitably high or low. See https://arxiv.org/abs/2211.14080
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        diameter: float,
        volume: float,
        power_limit: float,
        ambient_temperature: TimeseriesSpecifier,
        u_value: float | None = None,
        multiplexer_implementation: Implementation | str = Implementation.STRICT,
    ):
        """
        Create fully mixed heat storage component.

        :param name: Name of the component
        :param diameter: Diameter of the storage in m
        :param volume: Volume of the storage in m³
        :param power_limit: power limit in kW
        :param ambient_temperature: Ambient temperature in deg C
        :param u_value: Thermal transmittance in W/m²/K
        """
        if not isinstance(multiplexer_implementation, Implementation):
            multiplexer_implementation = Implementation(multiplexer_implementation)

        super().__init__(
            name=name,
            diameter=diameter,
            volume=volume,
            power_limit=power_limit,
            ambient_temperature=ambient_temperature,
            u_value=u_value,
            implementation=multiplexer_implementation,
        )

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        carrier: Heat = self.location.get_carrier(Heat)
        capacity_per_unit = self.volume * kJ_to_MWh(H2O_DENSITY * H2O_HEAT_CAPACITY)
        empty_level = carrier.reference_temperature

        solph_storage_arguments = {
            "nominal_storage_capacity": (
                max(carrier.temperature_levels) - carrier.reference_temperature
            )
            * capacity_per_unit
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
                "u_value is not implemented for this kond of storage"
            )

        self.build_multiplexer_structure(
            levels=carrier.levels,
            inputs=carrier.inputs,
            outputs=carrier.outputs,
            power_limit=self.power_limit,
            capacity_per_unit=capacity_per_unit,
            empty_level=empty_level,
            solph_storage_arguments=solph_storage_arguments,
        )
