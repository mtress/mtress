# -*- coding: utf-8 -*-

"""
Storage that has multiple heat layers that are all accessible at all times.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt

SPDX-License-Identifier: MIT
"""

from oemof import solph
from oemof.thermal import stratified_thermal_storage
from pyomo import environ as po

from mtress._base_mtress_nodes import AbstractTechnology
from mtress.carriers.heat import MassFlowHeat
from mtress.carriers.heat import TemperatureBus


H2O_DENSITY = 1000  # kg/m³


class LayeredHeatStorage(AbstractTechnology):
    """
    Layered heat storage.

    Layered storage, i.e. one subvolume per temperature level
    following https://doi.org/10.1016/j.apenergy.2022.118890.

    For simplification, an infitesimal subvolume for each temperature is
    and will be assumed to be always present, meaning that losses do not skip
    depleted layers and top-level losses will always consider the highest
    temeprature.
    Note that currently, only heat losses through the side are implemented,
    the storage only works for min_temperature == ambient_temperature.
    """

    def __init__(
        self,
        label,
        *,
        diameter: float,
        volume: float,
        temperature_levels: list[float],
        u_value=None,
        balanced: bool = True,
        parent_node=None,
        custom_properties=None,
    ):
        """
        Create layered heat storage component.

        :param diameter: Diameter of the storage in m
        :param volume: Volume of the storage in m³
        """
        super().__init__(
            label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        self._ambient_temperature = min(temperature_levels)
        self._u_value = u_value
        self.diameter = diameter

        self._build_core(temperature_levels, volume * H2O_DENSITY, balanced)


    def _build_core(self, temperature_levels, mass_content, balanced):
        """Build core structure of oemof.solph representation."""

        loss_flow = {}

        for temperature in sorted(temperature_levels):

                bus = self.subnode(
                    TemperatureBus,
                    temperature=temperature,
                    outputs=loss_flow,
                )

                self.subnode(
                    label=f"{temperature:.0f}",
                    node_type=solph.GenericStorage,
                    inputs={bus: MassFlowHeat()},
                    outputs={bus: MassFlowHeat()},
                    nominal_capacity=mass_content,
                    balanced=balanced,
                )

                if self._u_value is not None:
                    loss_flow = {bus: MassFlowHeat(maximum=1)}

    def add_constraints(self, model):
        """Add constraints to the model."""

        # >= && <= should be replaced by ==
        solph.constraints.shared_limit(
            model=model,
            quantity=model.GenericStorageBlock.storage_content,
            limit_name=f"{self.node.label}_storage_limit",
            components=self.storage_components.values(),
            weights=len(self.storage_components) * [1],
            upper_limit=self.volume * H2O_DENSITY,
            lower_limit=self.volume * H2O_DENSITY,
        )

        if self._u_value is not None:
            temperatures = list(self.storage_components.keys())

            # When a storage loses energy, in reality it will not direktly go
            # to the lowest temperature. We mimic this by (additional)
            # step-wise downshifting of the remaining heat.
            for lower_temperature, upper_temperature in zip(
                temperatures, temperatures[1:]
            ):

                loss_rate, _, fixed_losses = (
                    stratified_thermal_storage.calculate_losses(
                        self._u_value,
                        self.diameter,
                        upper_temperature,
                        lower_temperature,
                        self._ambient_temperature,
                    )
                )
                # fixed losses are only present for the top level
                if upper_temperature < temperatures[-1]:
                    fixed_losses = 0

                def equate_variables_rule(_, t):
                    return (
                        fixed_losses
                        + loss_rate
                        * (
                            model.GenericStorageBlock.storage_content[
                                self.storage_components[upper_temperature], t
                            ]
                        )
                    ) == model.flow[
                        self.buses[upper_temperature],
                        self.buses[lower_temperature],
                        t,
                    ]

                setattr(
                    model,
                    f"{self.node.label}_losses_{upper_temperature}",
                    po.Constraint(model.TIMESTEPS, rule=equate_variables_rule),
                )
