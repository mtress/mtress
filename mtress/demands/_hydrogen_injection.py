"""Hydrogen injection to Natural gas grid or 100% H2 Pipeline"""

from oemof.solph import Bus, Flow
from oemof.solph.components import Sink
from .._data_handler import TimeseriesSpecifier
from .._abstract_component import AbstractSolphComponent
from ..carriers import Hydrogen as HydrogenCarrier
from ._abstract_demand import AbstractDemand


class HydrogenInjection(AbstractDemand, AbstractSolphComponent):
    """
    Class representing a hydrogen injection into (a)Natural gas grid (b) Hydrogen Pipeline.

    Functionality:
    (a) Models the injection of hydrogen into the natural gas grid with the upper limit given by
    volume limit  multiplied by the natural gas flow time series. Due to current regulation,
    upper vol limit to the injection is restricted with 20% vol H2 w.r.t NG. This may or may not
    increase based on advancement/future regulations to come. In this case h2_pipeline is set to
    False (by default).

    Note: It's important to note that this simplified approach does not account for the
    complexities of the gas grid, such as pressure variations, pipeline capacities, gas
    composition (h2 presence already due to injection at other site within the network?),
    detailed safety considerations and engineering constraints, etc. It provides a rough
    estimation of the maximum allowable hydrogen volume based on the 20% volume limit
    and the volumetric flow rate of natural gas at the injection point.

   (b) This models the hydrogen injection into a 100% Hydrogen Pipeline. The inclusion of this
   feature in MTRESS is based on the recognition of various government initiatives in several
   developed countries, including Germany, where efforts are being made to establish pipelines
   dedicated to transporting 100% hydrogen. In Germany, there are already existing/in plan pipelines
   that have been repurposed or newly constructed to transport hydrogen exclusively. By
   setting the parameter h2_pipeline to True, this functionality can be enabled in MTRESS,
   allowing for the modeling of hydrogen injection into such pipelines.

   Procedure: Create a HydrogenInjection instance with the required parameters:
    - name: Name.
    - flow_time_series: (a) The time series of the natural gas flow rate (in kg/h).
                        (b) Maximum flow time series of hydrogen (kg/h) depending on the
                            injection capacity limit at that point/capacity of pipeline/
                            hydrogen demand in the region. It could also be set to
                            fix hydrogen demand time series based on the application.
    - pressure: (a) Pressure level of the hydrogen injection into natural gas grid.
                (b) Pressure level of the hydrogen injection into 100% H2 Pipeline.
    - volume_limit: (a) Volume limit for the hydrogen injection into NG grid (max= 20).
                    (b) It should be set to 100 when h2_pipeline = True.
    """

    def __init__(self, name: str, time_series: TimeseriesSpecifier, pressure: float, volume_limit: float, h2_pipeline: bool = False):
        """Initialize hydrogen energy carrier and add components."""
        super().__init__(name=name)

        self.time_series = time_series
        self.pressure = pressure
        self.volume_limit = volume_limit
        self.h2_pipeline = h2_pipeline

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        hydrogen_carrier = self.location.get_carrier(HydrogenCarrier)
        _, pressure = hydrogen_carrier.get_surrounding_levels(self.pressure)

        if pressure not in hydrogen_carrier.pressure_levels:
            raise ValueError("Pressure must be a valid pressure level")

        if self.h2_pipeline is False:
            if self.volume_limit > 20:
                raise ValueError("Provided vol. limit is more than the current hydrogen injection regulation, "
                                 "please reconsider reducing it to less than or equal to 20")

            natural_gas_flow = self._solph_model.data.get_timeseries(self.time_series)
            max_hydrogen_flow = natural_gas_flow * (self.volume_limit / 100)

            self.create_solph_component(
                label="sink",
                component=Sink,
                inputs={
                    hydrogen_carrier.outputs[self.pressure]: Flow(
                        nominal_value=1,
                        max=max_hydrogen_flow,
                    )
                },
            )

        else:
            if self.volume_limit != 100:
                raise ValueError("Hydrogen Pipeline should have volume_limit = 100")

            self.create_solph_component(
                label="sink",
                component=Sink,
                inputs={
                    hydrogen_carrier.outputs[self.pressure]: Flow(
                        nominal_value=1,
                        max=self._solph_model.data.get_timeseries(self.time_series),
                    )
                },
            )