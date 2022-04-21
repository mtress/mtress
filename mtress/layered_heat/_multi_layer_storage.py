# -*- coding: utf-8 -*-

"""
basic heat layer functionality

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: kehag Energiehandel GMbH
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Lucas Schmeling

SPDX-License-Identifier: MIT
"""
from oemof import solph
from oemof import thermal

from mtress.physics import (kilo_to_mega, kJ_to_MWh,
                            H2O_DENSITY, H2O_HEAT_CAPACITY,
                            TC_INSULATION)


class MultiLayerStorage:
    """
    Matrjoschka storage:
    One storage per temperature levels with shared resources.
    See https://arxiv.org/abs/2012.12664
    """
    def __init__(self,
                 diameter,
                 volume,
                 insulation_thickness,
                 ambient_temperature,
                 heat_layers,
                 label=""):
        """
        :param diameter: numeric scalar (in m)
        :param volume: numeric scalar (in m³)
        :param insulation_thickness: width of insulation (in m)
        :param ambient_temperature: numeric scalar or sequence (in °C)
        :param heat_layers: HeatLayers object
        """
        self._h_storage_comp = list()

        self.energy_system = heat_layers.energy_system
        self._temperature_levels = heat_layers.temperature_levels
        self._reference_temperature = heat_layers.reference_temperature

        self.heat_storage_volume = volume

        self._heat_storage_insulation = insulation_thickness

        self._loss_rate = {}
        self._fixed_losses = {"abs": {},
                              "rel": {}}

        self.in_flows = dict()
        self.out_flows = dict()
        self.content = dict()

        if len(label) > 0:
            self.label = label + '_'
        else:
            self.label = "s_heat_"

        for temperature in self._temperature_levels:
            temperature_str = "{0:.0f}".format(temperature)
            storage_label = self.label + temperature_str
            b_th_level = heat_layers.b_th[temperature]

            hs_capacity = self.heat_storage_volume * \
                          kJ_to_MWh((temperature
                                     - heat_layers.reference_temperature) *
                                    H2O_DENSITY *
                                    H2O_HEAT_CAPACITY)

            if self._heat_storage_insulation <= 0:
                hs_loss_rate = 0
                hs_fixed_losses_relative = 0
                hs_fixed_losses_absolute = 0
            else:
                (hs_loss_rate,
                 hs_fixed_losses_relative,
                 hs_fixed_losses_absolute) = (
                    thermal.stratified_thermal_storage.calculate_losses(
                        u_value=TC_INSULATION / self._heat_storage_insulation,
                        diameter=diameter,
                        temp_h=temperature,
                        temp_c=self._reference_temperature,
                        temp_env=ambient_temperature))

            # losses to the upper side of the storage will just leave the
            # storage for the uppermost level.
            # So, we neglect them for the others.
            if temperature != max(self._temperature_levels):
                hs_fixed_losses_relative = hs_fixed_losses_absolute = 0

            self._loss_rate[temperature] = hs_loss_rate
            self._fixed_losses["abs"][temperature] = hs_fixed_losses_absolute
            self._fixed_losses["rel"][temperature] = hs_fixed_losses_relative

            s_heat = solph.GenericStorage(
                label=storage_label,
                inputs={b_th_level: solph.Flow()},
                outputs={b_th_level: solph.Flow()},
                nominal_storage_capacity=hs_capacity,
                loss_rate=hs_loss_rate,
                fixed_losses_absolute=hs_fixed_losses_absolute,
                fixed_losses_relative=hs_fixed_losses_relative
            )
            self.in_flows[temperature] = (b_th_level.label, s_heat.label)
            self.out_flows[temperature] = (s_heat.label, b_th_level.label)
            self.content[temperature] = (s_heat.label, None)

            self._h_storage_comp.append(s_heat)
            self.energy_system.add(s_heat)

    def add_shared_limit(self, model):
        """
        :param model: solph.model
        """
        w_factor = [1 / kilo_to_mega(H2O_HEAT_CAPACITY
                                     * H2O_DENSITY
                                     * (temp - self._reference_temperature))
                    for temp in self._temperature_levels]

        solph.constraints.shared_limit(
            model, model.GenericStorageBlock.storage_content,
            self.label+'storage_limit', self._h_storage_comp, w_factor,
            upper_limit=self.heat_storage_volume)

    @property
    def combined_inflow(self):
        heat = 0
        for res in self.in_flows.values():
            heat += self.energy_system.results['main'][res][
                'sequences']['flow']

        return heat

    @property
    def combined_outflow(self):
        heat = 0
        for res in self.out_flows.values():
            heat += self.energy_system.results['main'][res][
                'sequences']['flow']

        return heat

    @property
    def loss_rate(self):
        """
        :return: loss rate
        """
        return self._loss_rate

    @property
    def fixed_losses(self):
        """
        :return: fixed losses
        """
        return self._fixed_losses
