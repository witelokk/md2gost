from dataclasses import dataclass


@dataclass(kw_only=True, frozen=True)
class RenderingSettings:
    debug: bool = False
    syntax_highlighting: bool
    title: str = None
    first_page: int = 1
