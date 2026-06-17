from typing import Literal

SPINE = Literal["left", "right", "top", "bottom"]
SPINES = list[SPINE] | tuple[SPINE] | set[SPINE]
