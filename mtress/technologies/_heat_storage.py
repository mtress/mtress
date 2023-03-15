"""MTRESS heat storages."""


from oemof.thermal import stratified_thermal_storage

from .._data_handler import TimeseriesSpecifier
from ..carriers import Heat
from ..physics import H2O_DENSITY, H2O_HEAT_CAPACITY, kJ_to_MWh
from ._abstract_technology import AbstractTechnology
from ._mixed_storage import AbstractMixedStorage

# Thermal conductivity of insulation material
TC_INSULATION = 0.04  # W / (m * K)

class AbstractHeatStorage(AbstractTechnology):
    """Abstract heat storage."""

    def __init__(
        self,
        name: str,
        diameter: float,
        volume: float,
        insulation_thickness: float,
        ambient_temperature: TimeseriesSpecifier,
    ):
        super().__init__(name)

        self.diameter = diameter
        self.volume = volume
        self.insulation_thickness = insulation_thickness
        self.ambient_temperature = ambient_temperature


class MixedHeatStorage(AbstractHeatStorage, AbstractMixedStorage):
    """Fully mixed heat storage."""

    def __init__(self, name: str, diameter: float, volume: float, insulation_thickness: float, ambient_temperature: TimeseriesSpecifier):
        super().__init__(name, diameter, volume, insulation_thickness, ambient_temperature)

        self.carrier : Heat = self.location.get_carrier(Heat)
        self.capacity_per_unit = self.volume * kJ_to_MWh(H2O_DENSITY * H2O_HEAT_CAPACITY)
        self.empty_level = self.carrier.reference_temperature

    def build_core(self):
        """Build solph core structure."""
        
        # TODO: Check units
        self.solph_storage_arguments = {}
        

        if self.insulation_thickness <= 0:
            loss_rate = 0
            fixed_losses_relative = 0
            fixed_losses_absolute = 0
        else:
            (
                loss_rate,
                fixed_losses_relative,
                fixed_losses_absolute,
            ) = stratified_thermal_storage.calculate_losses(
                u_value=TC_INSULATION / self.insulation_thickness,
                diameter=self.diameter,
                temp_h=30,
                temp_c=0,
                temp_env=self._solph_model.data.get_timeseries(
                    self.ambient_temperature
                ),
            )

        return super().build_core()


 