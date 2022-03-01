# -*- coding: utf-8 -*-

"""
pv wrapper for generic RenewableElectricitySource

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt

SPDX-License-Identifier: MIT
"""

import pvlib

from ._renewable_electricity_source import RenewableElectricitySource


class Photovoltaics(RenewableElectricitySource):
    """
    photovoltaics wrapper for generic RenewableElectricitySource
    """

    def __init__(
        self,
        pv_system_params,
        simulation_data,
        funding,
        out_bus_internal,
        out_bus_external,
        label,
        energy_system,
    ):
        self._loc = pvlib.location.Location(
            latitude=pv_system_params["latitude"],
            longitude=pv_system_params["longitude"],
        )

        module_parameters = pv_system_params.get(
            "module_parameters", dict(pdc0=1, gamma_pdc=-0.004)
        )
        temperature_model_parameters = pv_system_params.get(
            "temperature_model_parameters", dict(a=-3.56, b=-0.075, deltaT=3)
        )

        self._system = pvlib.pvsystem.PVSystem(
            surface_tilt=pv_system_params["surface_tilt"],
            surface_azimuth=pv_system_params["surface_azimuth"],
            module_parameters=module_parameters,
            temperature_model_parameters=temperature_model_parameters,
            name=label,
            inverter_parameters=dict(pdc0=3),
        )

        self._mc = pvlib.modelchain.ModelChain(
            self._system, self._loc, aoi_model="physical", spectral_model="no_loss"
        )

        self._weather = simulation_data.get(
            "weather", self._loc.get_clearsky(energy_system.timeindex)
        )

        self._mc.run_model(self._weather)

        self.nominal_power = pv_system_params.get("nominal_power")
        self.specific_generation = self._mc.results.ac

        super().__init__(
            self.nominal_power,
            self.specific_generation,
            funding,
            out_bus_internal,
            out_bus_external,
            label,
            energy_system,
        )
