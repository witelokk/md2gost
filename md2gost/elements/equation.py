from dataclasses import dataclass, field

from .caption import Caption


@dataclass
class Equation:
    caption: Caption = None
    latex: str = ""
