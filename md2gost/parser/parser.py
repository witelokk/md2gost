from abc import ABC, abstractmethod

from ..elements import Element


class Parser(ABC):
    @abstractmethod
    def parse(self, text: str, source_dir: str) -> list[Element]:
        """
        Parses given text
        :param text: source text
        :param source_dir: directory of source file (used to resolve relative paths)
        :returns: parsed elements
        """
