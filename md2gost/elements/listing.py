from dataclasses import dataclass, field
from pygments import highlight
from pygments.formatter import Formatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

from .caption import Caption
from .element import Element
from .run import Run


class RunsPygmentsFormatter(Formatter):
    def __init__(self, **options):
        Formatter.__init__(self, style="sas", **options)
        self._styles = {}

        for token, style in self.style:
            self._styles[token] = style

        self.lines = []

    def _add_run_to_last_line(self, text, style):
        self.lines[-1].append(Run(text, style["bold"] or None, style["italic"] in style or None,
                                  color=style["color"] if style["color"] else None))

    def format(self, tokensource, outfile):
        self.lines.append([])
        for ttype, value in tokensource:
            style = self._styles[ttype]
            lines = iter(value.split("\n"))
            self._add_run_to_last_line(next(lines), style)
            for line in lines:
                self.lines.append([])
                self._add_run_to_last_line(line, style)
        # self.lines.pop(-1)  # remove last empty line


@dataclass
class Listing(Element):
    caption: Caption = None
    language: str = ""
    code: str = ""

    def get_lines(self, highlighted=False) -> list[list[Run]]:
        try:
            lexer = get_lexer_by_name(self.language)
        except ClassNotFound:
            lexer = None

        if not highlighted or not lexer:
            return [[Run(line)] for line in self.code.split("\n")]
        else:
            formatter = RunsPygmentsFormatter()
            highlight(self.code, lexer, formatter)
            return formatter.lines
