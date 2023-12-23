from .parser import Parser
from md2gost.parser.markdown import MarkdownParser


def create_parser_by_extension(extension: str) -> Parser | None:
    """Creates suitable parser for file based on its extension.
            Returns None if there is no parser for the extension."""

    if extension in ("md", "markdown"):
        return MarkdownParser()

    return None
