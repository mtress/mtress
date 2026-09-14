# -*- coding: utf-8 -*-

"""
Storage that has multiple heat layers that are all accessible at all times.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Jann Launer
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: oemof e.V.

SPDX-License-Identifier: MIT
"""

import numpy as np

from oemof import solph
from pyomo import environ as po

from mtress._base_mtress_nodes import AbstractTechnology
from mtress.carriers import HeatCarrier
from mtress.carriers.heat import MassFlowHeat
from mtress.carriers.heat import TemperatureBus


H2O_SPECIFIC_HEAT_CAPACITY = 4179  # J/kg/K @ 50 °C
H2O_DENSITY = 988 # kg/m³ @ 50 °C


class LayeredHeatStorage(AbstractTechnology):
    """
    Layered heat storage.

    Layered storage, i.e. one subvolume per temperature level.
    The formulation is is more detailed than a warehouse model
    but less detailed than e.g. the formulation found in
    https://doi.org/10.1016/j.apenergy.2022.118890.

    For simplification, an infitesimal subvolume for each temperature is
    and will be assumed to be always present.
    This way, losses can contribute to (previously) depleted layers.
    Note that currently only heat losses through the side are implemented,
    and the the storage assumes min_temperature == ambient_temperature.
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
        self._diameter = diameter

        self._build_core(temperature_levels, volume * H2O_DENSITY, balanced)


    def _build_core(self, temperature_levels, mass_content, balanced):
        """Build core structure of oemof.solph representation."""

        loss_flow = {}

        for temperature in sorted(temperature_levels):

                bus = self.subnode(
                    TemperatureBus,
                    local_name=f"b_{temperature:.0f}",
                    temperature=temperature,
                    outputs=loss_flow,
                )
                self.inbound_interfaces.add(bus)
                self.outbound_interfaces.add(bus)

                self.subnode(
                    solph.components.GenericStorage,
                    local_name=f"s_{temperature:.0f}",
                    inputs={bus: MassFlowHeat()},
                    outputs={bus: MassFlowHeat()},
                    nominal_capacity=mass_content,
                    balanced=balanced,
                    custom_properties={"temperature": temperature},
                )

                if self._u_value is not None:
                    loss_flow = {bus: MassFlowHeat(maximum=1)}

    def _loss_rate(self) -> float:
        r"""
        :math:`\beta = U \frac{4}{d\rho c}\Delta t`
        """
        return(
            4
            * self._u_value
            / (self._diameter * H2O_DENSITY * H2O_SPECIFIC_HEAT_CAPACITY)
            * 3600  # Ws to Wh
        )

    def _fixed_losses_relative(self, *, temp_h, temp_c) -> float:
        r"""
        :math:`\gamma = U \frac{4}{d\rho c \Delta T_{HC}}\Delta T_{C0}\Delta t`
        """
        return (
            4
            * self._u_value
            * (temp_c - self._ambient_temperature)
            * 1
            / ((self._diameter * H2O_DENSITY * H2O_SPECIFIC_HEAT_CAPACITY) * (temp_h - temp_c))
            * 3600  # Ws to Wh
        )

    def _fixed_losses_absolute(self, *, temp_h, temp_c) -> float:
        r"""
        :math:`\delta = U \frac{\pi d^2}{4}\Big(\Delta T_{H0} + \Delta T_{C0}\Big)\Delta t`
        """
        return (
            0.25
            * self._u_value
            * np.pi
            * self._diameter**2
            * (temp_h + temp_c - 2 * self._ambient_temperature)
        )

    def _connect_to_carrier(self, heat_carrier: HeatCarrier):
        for inbound_interface in self.inbound_interfaces[TemperatureBus]:
            [inbound_node] = heat_carrier.nodes_to_connect(inbound_interface)
            # We assume exactly one matching counterpart. More complex cases
            # (e.g. crossing levels) should be handled in the HeatCarrier.
            inbound_node.outputs[inbound_interface] = MassFlowHeat()
            inbound_node.inputs[inbound_interface] = MassFlowHeat()


    def establish_interconnections(self):
        self._connect_to_carrier(self.parent.get_carrier(HeatCarrier))


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
                    LayeredHeatStorage.calculate_losses(
                        self._u_value,
                        self._diameter,
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
