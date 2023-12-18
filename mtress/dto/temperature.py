from dataclasses import dataclass, field


@dataclass
class Temperatures:
    reference: float = 30  # C°
    dhw: float = 60  # C°
    heat_drop_exchanger_dhw: float = 5  # C°
    forward_flow: float = 40 #  C°
    backward_flow: float = 30 # C°
    additional: list[float] = field(default_factory=list) # C°
