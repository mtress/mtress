from oemof.network import Node

from mtress._constants import EnergyType
from mtress.carriers import ElectricityCarrier


def test_basic_initialisation():
    label = "ElectricityCarrier"
    ec = ElectricityCarrier(label=label)
    assert ec.label == label

    assert len(ec.inbound_interfaces[EnergyType.ELECTRICITY]) == 2
    assert len(ec.outbound_interfaces[EnergyType.ELECTRICITY]) == 2
