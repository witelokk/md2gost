import re
from re import Match

from marko.block import BlockElement
from marko.source import Source


class Heading(BlockElement):
    """Heading element: (### Hello\n)

    Asterisk before text means that headings is unnumbered"""

    priority = 6
    pattern = re.compile(
        r" {0,3}(#{1,6})((?=\s)[^\n]*?|[^\n\S]*)(?:(?<=\s)(?<!\\)#+)?[^\n\S]*$\n?",
        flags=re.M,
    )
    override = True

    def __init__(self, match: Match[str]) -> None:
        self.level = len(match.group(1))
        inline_body = match.group(2).strip()
        self.numbered = not (inline_body[0] == "*")
        if not self.numbered:
            inline_body = inline_body[1:]
        self.inline_body = inline_body

    @classmethod
    def match(cls, source: Source) -> Match[str] | None:
        return source.expect_re(cls.pattern)

    @classmethod
    def parse(cls, source: Source) -> Match[str] | None:
        m = source.match
        source.consume()
        return m
