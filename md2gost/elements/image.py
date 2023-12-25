from dataclasses import dataclass, field
from urllib.parse import unquote

from .caption import Caption


@dataclass
class Image:
    caption: Caption = None
    _path: str = None

    @property
    def path(self) -> str:
        return unquote(self._path)
