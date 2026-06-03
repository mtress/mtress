"""This module provide gas carrier in MTRESS"""

from oemof.solph import Bus, Flow

from .._energy_types import EnergyType
from ._layered_carrier import AbstractLayeredCarrier


class GasCarrier(AbstractLayeredCarrier):
    """
    GasCarrier is the container for different types of gases, which
    considers the gas properties from dataclass Gas. All gas flows,
    be it Hydrogen, Natural gas, Biogas or Bio-Methane, are considered
    to be in kg to maintain resiliency in the modelling.

    Parameters
    ----------
    gas: in kg
    pressure: in bar
    """

    def __init__(
        self,
        label,
        *,
        parent_node=None,
        custom_properties=None,
    ):
        """Initialize carrier."""
        super().__init__(
            label,
            parent_node=parent_node,
            custom_properties=custom_properties,
        )

        self._distribution = {}

        # overwrite default list
        self._levels = {}

        self._build_core()

    def get_surrounding_levels(self, gas, pressure_level):
        """Get the next bigger and smaller level for the specified gas."""
        return self._get_surrounding_levels(pressure_level, self._levels[gas])

    @property
    def pressure_levels(self):
        """Return input_pressure level of gas carrier"""
        return self._levels

    def _build_core(self):
        """Build core structure of oemof.solph representation."""

        self.inbound_interfaces[EnergyType.GAS] = self.subnodes
        self.outbound_interfaces[EnergyType.GAS] = self.subnodes

    # @property
    # def inputs(self):
    #     return self.distribution

    # @property
    # def outputs(self):
    #     return self.distribution

    @property
    def distribution(self):
        return self._distribution

    def establish_interconnections(self):
        # collect fixed gas types and pressures levels
        interfaces = self.parent.get_interfaces(EnergyType.GAS)
        gas_pressure = {}
        for i in interfaces:
            g = i.custom_properties.get("gas")
            p = i.custom_properties.get("pressure")
            if None not in (g, p):  # both need to be present
                gas_pressure.setdefault(g, [])
                gas_pressure[g].append(p)

        for gas, pressures in gas_pressure.items():
            p_low = None
            self.distribution.setdefault(gas, {})
            for p in sorted(pressures):
                # check if first bus for gas type
                if not self.distribution[gas]:
                    g_bus = self.subnode(
                        Bus,
                        local_name=f"{gas.name}_{p}",
                        custom_properties={
                            "gas": gas,
                            "pressure": p,
                        },
                    )
                else:
                    g_bus = self.subnode(
                        Bus,
                        local_name=f"{gas.name}_{p}",
                        custom_properties={
                            "gas": gas,
                            "pressure": p,
                        },
                        outputs={
                            self.distribution[gas][p_low]: Flow(
                                custom_properties={
                                    "unit": "kg/h",
                                    "energy_type": EnergyType.GAS,
                                }
                            )
                        },
                    )
                self.distribution[gas][p] = g_bus

                # prepare next iteration
                p_low = p

                # update levels
                self._levels.setdefault(gas, [])
                self._levels[gas].append(p)
