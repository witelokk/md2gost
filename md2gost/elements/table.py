from dataclasses import dataclass, field
from typing import Literal

from . import Image
from .caption import Caption
from .paragraph import Paragraph

@dataclass
class TableCell:
    items: list[list[Paragraph | Image]] = field(default_factory=list)
    alignment: Literal["left", "right", "center", "justify"] = "justify"


@dataclass
class TableRow:
    cells: list[TableCell] = field(default_factory=list)


@dataclass
class Table:
    rows: list[TableRow] = field(default_factory=list)
    caption: Caption = None

    @property
    def rows_count(self):
        return len(self.rows)

    @property
    def cols_count(self):
        return max(len(row.cells) for row in self.rows)
