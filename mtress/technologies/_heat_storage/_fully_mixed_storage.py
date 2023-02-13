# -*- coding: utf-8 -*-

"""
Storage that has a homogenious temperature distribution.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

SPDX-License-Identifier: MIT
"""
from oemof.solph import Bus, Flow
from oemof.solph.components import GenericStorage

from mtress._data_handler import TimeseriesSpecifier
from mtress._storage_level_constraint import storage_level_constraint
from mtress.carriers import Heat
from mtress.physics import H2O_DENSITY, H2O_HEAT_CAPACITY, kJ_to_MWh

from ._abstract_heat_storage import AbstractHeatStorage


class FullyMixedHeatStorage(AbstractHeatStorage):
    """
    Fully mixed heat storage.

    Fully mixed heat storage that makes sure access is only when temperatures
    are suitably high or low. See https://arxiv.org/abs/2211.14080
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
        Create fully mixed heat storage component.

        :param diameter: Diameter of the storage in m
        :param volume: Volume of the storage in m³
        :param insulation_thickness: Insulation thickness in m
        :param ambient_temperature: Ambient temperature in deg C
        """
        super().__init__(
            name=name,
            diameter=diameter,
            volume=volume,
            ambient_temperature=ambient_temperature,
            u_value=u_value
        )

        self.storage_component = None
        self.multiplexer_bus = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        # Create storage components according to the temperature levels defined
        # by the heat carrier object
        heat_carrier = self.location.get_carrier(Heat)

        self.multiplexer_bus = self._solph_model.add_solph_component(
            mtress_component=self,
            label="multiplexer",
            solph_component=Bus,
        )

        capacity = self.volume * kJ_to_MWh(
            (max(heat_carrier.temperature_levels) - heat_carrier.reference_temperature)
            * H2O_DENSITY * H2O_HEAT_CAPACITY
        )

        if self.u_value is None:
            loss_rate = 0
            fixed_losses_relative = 0
            fixed_losses_absolute = 0
        else:
            raise NotImplementedError("u_value is not implemented for this kond of storage")

        self.storage_component = self._solph_model.add_solph_component(
            mtress_component=self,
            label="storage",
            solph_component=GenericStorage,
            inputs={self.multiplexer_bus: Flow()},
            outputs={self.multiplexer_bus: Flow()},
            nominal_storage_capacity=capacity,
            loss_rate=loss_rate,
            fixed_losses_absolute=fixed_losses_absolute,
            fixed_losses_relative=fixed_losses_relative,
        )


    def add_constraints(self):
        """Add constraints to the model."""
        heat_carrier = self.location.get_carrier(Heat)
        temperature_levels = heat_carrier.temperature_levels
        reference_temperature = heat_carrier.reference_temperature
        highest_temperature = max(temperature_levels)

        input_levels = {}
        output_levels = {}
        for temperature in temperature_levels:
            input_levels[heat_carrier.outputs[temperature]] = (
                (temperature - reference_temperature)/highest_temperature
            )
            output_levels = heat_carrier.inputs[temperature] = (
                (temperature - reference_temperature)/highest_temperature
            )

        storage_level_constraint(
            model=self._solph_model.model,
            name=self._solph_model.get_label(self, "level_contraint"),
            storage_component=self.storage_component,
            multiplexer_bus=self.multiplexer_bus,
            input_levels=input_levels,
            output_levels=output_levels,
        )
