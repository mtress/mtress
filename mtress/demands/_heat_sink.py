from oemof.solph import Flow
from oemof.solph.components import Sink
from .._abstract_component import AbstractSolphRepresentation
from ..carriers import Heat
from ._abstract_demand import AbstractDemand


class HeatSink(AbstractDemand, AbstractSolphRepresentation):
    """
    Heat Sink is a demand component to dump any excess heat from Electrolyser or Fuel Cell CHP that are not
    utilized in heat network. This will avoid infeasibility in optimization caused due to excess heat production
    in the energy system (less than the heat demand in your energy system). Both PEM Electrolyser and Fuel Cell
    generates thermal energy that is being utilized to increase their overall efficiency. It finds its application
    where electricity and heat network are sector-coupled. User need to insert the temperature level of the sink
    irrespective of temperature level of the EM Electrolyser and Fuel Cell. It would be more practical to give
    temperature level closer or equal to temperature level or either PEM Ely or Fuel Cell.
    """

    def __init__(
        self,
        name: str,
        temperature_levels: float = None,
    ):
        """
        Initialize Heat Sink.
        :param name: Name of the component/demand
        :param temperature_levels: Temperature level of Heat Sink
        """
        super().__init__(name=name)

        self.temperature_levels = temperature_levels
        self.heat_sink_bus = None

    def build_core(self):
        """Build core structure of oemof.solph representation."""
        heat_carrier = self.location.get_carrier(Heat)

        _, temperature_levels = heat_carrier.get_surrounding_levels(
            self.temperature_levels
        )

        if temperature_levels not in heat_carrier.temperature_levels:
            raise ValueError("Temperature must be a valid Temperature level")

        self.create_solph_node(
            label="Sink",
            node_type=Sink,
            inputs={heat_carrier.outputs[temperature_levels]: Flow()},
        )
