from dataclasses import dataclass, field

from .caption import Caption


@dataclass
class Image:
    caption: Caption = None
    path: str = None
