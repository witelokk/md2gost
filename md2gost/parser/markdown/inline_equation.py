from marko.inline import InlineElement
from re import Match


class InlineEquation(InlineElement):
    """Represents inline formula element

    Syntax: \\( y = x \\)"""

    pattern = r"\$(.*?)\$"
    priority = 6

    def __init__(self, match: Match[str]):
        self.latex_equation = match.group(1)
