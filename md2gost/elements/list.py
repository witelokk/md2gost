from __future__ import annotations
from dataclasses import dataclass, field

from .paragraph import Paragraph


@dataclass
class ListItem:
    elements: list[Paragraph | List] = field(default_factory=list)


@dataclass
class List:
    ordered: int = False
    items: list[ListItem] = field(default_factory=list)
