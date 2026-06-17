from dataclasses import dataclass
from typing import Literal

SPINE = Literal["left", "right", "top", "bottom"]
SPINES = list[SPINE] | tuple[SPINE] | set[SPINE]

@dataclass
class LabelCfg():
    label: str
    fontsize: int = 12
