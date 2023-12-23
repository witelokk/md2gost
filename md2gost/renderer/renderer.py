import sys
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Collection

from .redering_settings import RenderingSettings
from ..elements import Element, List, Heading, TOC, Image, Table, Listing, Equation


class Renderer(ABC):
    def __init__(self, elements: Collection[Element]):
        self._elements = elements

        self.__rendered = False

        self._reference_numbers: dict[str, int] = {}
        self._headings = []

    @abstractmethod
    def _render(self):
        pass

    @abstractmethod
    def save(self, path: str):
        """Writes rendered file to path"""

    def render(self):
        """
        Renders elements. It can be executed only once.
        """

        if self.__rendered:
            raise RuntimeError("Already rendered!")

        self.__number_elements(self._elements)

        # set text to references
        # for element in elements:
        #     if hasattr(element, "runs"):
        #         for run in element.runs:
        #             if run.reference_target:
        #                 if run.reference_target not in self._reference_numbers:
        #                     print(f"Не найдена ссылка {run.reference_target}", file=sys.stderr)
        #                 else:
        #                     run.text = str(self._reference_numbers[run.reference_target])
        #     if isinstance(element, List):
        #         for item in element.items:
        #             if hasattr(item, "runs"):
        #                 for run in item.runs:
        #                     if run.reference_target:
        #                         if run.reference_target not in self._reference_numbers:
        #                             print(f"Не найдена ссылка {run.reference_target}", file=sys.stderr)
        #                         else:
        #                             run.text = str(self._reference_numbers[run.reference_target])

        self._render()

        self.__rendered = True

    def __number_elements(self, elements):
        """Numbers elements such as images, listing, equations and tables"""
        numbering = defaultdict(lambda: 0)
        toc = False
        for element in elements:
            if isinstance(element, (Image, Table, Listing, Equation)):
                numbering[type(element)] += 1
                self._reference_numbers[element.caption.id] = numbering[type(element)]
                # print(element.caption.id, element)
            if isinstance(element, TOC):
                toc = True
            if toc and isinstance(element, Heading):
                self._headings.append(element)
            if isinstance(element, List):
                for item in element.items:
                    self.__number_elements(item.elements)
