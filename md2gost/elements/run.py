from dataclasses import dataclass


@dataclass
class Run:
    _text: str = ""
    bold: bool = False
    italic: bool = False
    strike_through: bool = False
    color: str = None
    url: str = None
    reference_target: str = None

    @property
    def text(self):
        return self._text.replace("\t", "    ") if self._text else ""

    @text.setter
    def text(self, value):
        self._text = value
