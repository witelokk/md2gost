import re

from marko.block import BlockElement
from marko.source import Source
from re import Match


class Equation(BlockElement):
    """Represents formula element

    Syntax: $$ 2 + 2 = 4 $$"""

    pattern = re.compile(r"\$\$([\S\s]*?)\$\$", re.M)

    def __init__(self, match: Match[str]):
        self.latex_equation = match.group(1).strip()

    @classmethod
    def match(cls, source: Source) -> Match[str] | None:
        return source.expect_re(cls.pattern)

    @classmethod
    def parse(cls, source: Source) -> Match[str] | None:
        m = source.match
        source.consume()
        return m
