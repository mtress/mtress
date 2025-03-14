# -*- coding: utf-8 -*-

"""
PV wrapper for generic RenewableElectricitySource.

SPDX-FileCopyrightText: Deutsches Zentrum für Luft und Raumfahrt
SPDX-FileCopyrightText: Patrik Schönfeldt
SPDX-FileCopyrightText: Sunke Schlüters

SPDX-License-Identifier: MIT
"""


import logging
from typing import Dict, Tuple

import pandas as pd
import pvlib

from .._data_handler import TimeseriesSpecifier, TimeseriesType
from ._renewable_electricity_source import RenewableElectricitySource

_LOGGER = logging.getLogger(__name__)


def calculate_dni(weather: pd.DataFrame, location: pvlib.location.Location):
    """
    Calculate DNI from GHI and DHI.

    :param weather: Dataframe with weather parameters.
    :type weather: class:`pandas.DataFrame`
    :param location: Location of PV system
    :type location: class:`pvlib.location.Location`

    Parameters
    ----------
    ghi : array-like
        Global horizontal irradiance in W/m².

    solar_zenith : array-like
        True (not refraction-corrected) solar_zenith angles in °.
        0 <= solar_zenith <= 90

    times : DatetimeIndex

    pressure : float or array-like, default 101325.0
        The site pressure in Pascal. Pressure may be measured or an
        average pressure may be calculated from site altitude.

    temp_dew : None, float, or array-like, default None
        Surface dew point temperatures, in °C. Values of temp_dew
        may be numeric or NaN. Any single time period point with a
        temp_dew=NaN does not have dew point improvements applied. If
        temp_dew is not provided, then dew point improvements are not
        applied.

    :return: DNI values in W/m²
    :rtype: class:`pandas.Series`
    """
    solar_position = location.get_solarposition(
        times=weather.index,
        pressure=weather["pressure"],
        temperature=weather["temp_air"],
        method="nrel_numpy",
    )

    dni = pvlib.irradiance.dirint(
        ghi=weather["ghi"],
        solar_zenith=solar_position["zenith"],
        times=weather.index,
        pressure=weather["pressure"],
        use_delta_kt_prime=True,
        temp_dew=weather["temp_dew"],
    )

    # Set dni to zero for all time steps when the elevation is negative,
    # i.e. when the sun is behind the horizon
    dni.loc[solar_position["elevation"] <= 0] = 0

    return dni


class Photovoltaics(RenewableElectricitySource):
    """Photovoltaics wrapper for generic RenewableElectricitySource."""

    def __init__(
        self,
        name: str,
        location: pvlib.location.Location | Tuple[float, float],
        nominal_power: float,
        weather: Dict[str, TimeseriesSpecifier] | pd.DataFrame = None,
        surface_tilt: float = None,
        surface_azimuth: float = None,
        pv_system: pvlib.pvsystem.PVSystem = None,
        fixed: bool = True,
    ):  # pylint: disable=too-many-arguments
        """
        Initialize photovoltaics component.

        :param name: Name of the component.
        :param location: Geographical location of the system.
        :param nominal_power: Nominal power of the system (in W).
        :param weather: Weather time series.
        :param surface_tilt: Tilt of the system.
        :param surface_azimuth: Azimuth of the system.
        :param pv_system: PV system specification.
        """
        super().__init__(
            name=name,
            nominal_power=nominal_power,
            specific_generation=None,
            fixed=fixed,
        )

        if not isinstance(location, pvlib.location.Location):
            latitude, longitude = location
            location = pvlib.location.Location(latitude, longitude)

        self.geo_location = location

        self.weather = weather

        self.surface_tilt = surface_tilt
        self.surface_azimuth = surface_azimuth

        if pv_system is None:
            pv_system = pvlib.pvsystem.PVSystem(
                module_parameters=dict(pdc0=1, gamma_pdc=-0.004),
                temperature_model_parameters=dict(a=-3.56, b=-0.075, deltaT=3),
                inverter_parameters=dict(pdc0=1),
                racking_model="close_mount",
                module_type="glass_glass",
            )

        self.pv_system = pv_system

    def _prepare_weather_data(self):
        if self.weather is None:
            _LOGGER.warning("No weather data provided, taking clearsky data")
            return self.geo_location.get_clearsky(
                self._solph_model.data.timeindex
            )

        weather = pd.DataFrame()
        for col in ["ghi", "dhi"]:
            if col not in self.weather:
                raise KeyError(f"{col} data missing")

            weather[col] = self._solph_model.data.get_timeseries(
                self.weather[col], kind=TimeseriesType.INTERVAL
            )

        if "dni" not in weather:
            for col in ["temp_air", "temp_dew", "pressure"]:
                if col not in self.weather:
                    raise KeyError(
                        f"{col} required if dni is not provided missing"
                    )

                weather[col] = self._solph_model.data.get_timeseries(
                    self.weather[col], kind=TimeseriesType.INTERVAL
                )

            weather["dni"] = calculate_dni(weather, self.geo_location)
        else:
            weather["dni"] = self._solph_model.data.get_timeseries(
                self.weather["dni"], kind=TimeseriesType.INTERVAL
            )

        for col in ["temp_air", "wind_speed"]:
            if col not in self.weather:
                _LOGGER.warning("{col} not provided, using pvlib defaults")
            else:
                weather[col] = self._solph_model.data.get_timeseries(
                    self.weather[col], kind=TimeseriesType.INTERVAL
                )

        return weather

    def build_core(self):
        """Calculate generation time series and build solph structure."""
        for attr in ["surface_tilt", "surface_azimuth"]:
            if val := getattr(self, attr) is not None:
                if len(self.pv_system.arrays) > 1:
                    raise ValueError(
                        f"Can assign {attr} for only one PV array"
                    )

                setattr(self.pv_system.arrays[0].mount, attr, val)

        model_chain = pvlib.modelchain.ModelChain(
            self.pv_system,
            self.geo_location,
            aoi_model="physical",
            spectral_model="no_loss",
        )

        weather = self._prepare_weather_data()
        model_chain.run_model(weather)

        self.specific_generation = model_chain.results.ac

        return super().build_core()
