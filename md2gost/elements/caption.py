from uuid import uuid4
from dataclasses import dataclass, field

from .run import Run


@dataclass
class Caption:
    id: str = field(default_factory=lambda: uuid4().hex)
    runs: list[Run] = field(default_factory=list)
