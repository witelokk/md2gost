from marko.block import BlockElement
from marko.source import Source
from re import Match


class TOC(BlockElement):
    """Represents TOC field

    Syntax: [TOC]"""

    pattern = r"\[(TOC)\]+"

    def __init__(self, match: Match[str]):
        pass

    @classmethod
    def match(cls, source: Source) -> Match[str] | None:
        return source.expect_re(cls.pattern)

    @classmethod
    def parse(cls, source: Source) -> Match[str] | None:
        m = source.match
        source.consume()
        return m
