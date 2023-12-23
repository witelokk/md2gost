import os.path
import sys
from collections.abc import Generator
from functools import singledispatchmethod
from uuid import uuid4

from md2gost import elements
from md2gost.elements import TOC, TableCell, Run
from md2gost.elements.caption import Caption
from . import extended_markdown

from md2gost.parser.parser import Parser


class MarkdownParser(Parser):
    def __init__(self):
        self._caption = Caption()

    def parse(self, text, relative_path_dir: str) -> list[elements.Element]:
        parsed_elements = []
        marko_parsed = extended_markdown.markdown.parse(text)
        for marko_element in marko_parsed.children:
            if isinstance(marko_element, extended_markdown.Caption):
                self._caption = Caption(marko_element.id, list(self._create_runs(marko_element.children)))
                continue

            if isinstance(marko_element, extended_markdown.BlankLine):
                continue

            parsed_elements.extend(self._parse_marko_element(marko_element, relative_path_dir))

            self._caption = Caption()
        return parsed_elements

    @singledispatchmethod
    def _parse_marko_element(self, marko_element: extended_markdown.BlockElement, relative_path_dir: str)\
            -> Generator[elements.Element, None, None]:
        print(f"Can't parse block {type(marko_element)}", file=sys.stderr)
        yield from []

    @_parse_marko_element.register
    def _(self, marko_paragraph: extended_markdown.Paragraph | extended_markdown.TableCell, relative_path_dir: str):
        paragraph = elements.Paragraph()
        paragraph.runs = list(self._create_runs(marko_paragraph.children))
        if "".join([run.text for run in paragraph.runs]).strip():
            yield paragraph
        yield from self._extract_images(marko_paragraph, relative_path_dir)

    @_parse_marko_element.register
    def _(self, marko_heading: extended_markdown.Heading | extended_markdown.SetextHeading, relative_path_dir: str):
        heading = elements.Heading()
        heading.level = marko_heading.level
        heading.numbered = marko_heading.numbered

        heading.runs = list(self._create_runs(marko_heading.children))

        yield heading

    @_parse_marko_element.register
    def _(self, _: extended_markdown.ThematicBreak | extended_markdown.LinkRefDef, relative_path_dir: str):
        yield from []  # ignore

    @_parse_marko_element.register
    def _(self, marko_code_block: extended_markdown.CodeBlock | extended_markdown.FencedCode, relative_path_dir: str):
        listing = elements.Listing()

        listing.language = marko_code_block.lang
        listing.caption = self._caption
        listing.code = "\n".join(child.children for child in marko_code_block.children).removesuffix("\n")

        yield listing

    @_parse_marko_element.register
    def _(self, marko_equation: extended_markdown.Equation, relative_path_dir: str):
        equation = elements.Equation()
        equation.latex = marko_equation.latex_equation
        equation.caption = self._caption
        yield equation

    @_parse_marko_element.register
    def _(self, marko_table: extended_markdown.Table, relative_path_dir: str):
        table = elements.Table()
        table.caption = self._caption
        for marko_row in marko_table.children:
            row = elements.TableRow()
            for marko_cell in marko_row.children:
                row.cells.append(TableCell(list(self._parse_marko_element(marko_cell, relative_path_dir)),
                                           marko_cell.align or "justify"))
            table.rows.append(row)
        yield table

    @_parse_marko_element.register
    def _(self, _: extended_markdown.TOC, relative_path_dir: str):
        yield TOC()

    @_parse_marko_element.register
    def _(self, marko_list: extended_markdown.List, relative_path_dir: str):
        list_ = elements.List(ordered=marko_list.ordered)

        for marko_list_item in marko_list.children:
            list_item = elements.ListItem()
            for child in marko_list_item.children:
                list_item.elements.extend(self._parse_marko_element(child, relative_path_dir))
                # if isinstance(child, extended_markdown.List):
                #     list_item.elements.append += self._parse_marko_element(child)
                # elif isinstance(child, extended_markdown.Paragraph | extended_markdown.Heading):
                #     RenderableFactory._create_runs(item, child.children)
            list_.items.append(list_item)

        yield list_

    @_parse_marko_element.register
    def _(self, _: extended_markdown.BlankLine, relative_path_dir: str):
        yield from []  # ignore

    @staticmethod
    def _extract_images(marko_paragraph: extended_markdown.Paragraph, relative_path_dir: str)\
            -> Generator[elements.Image, None, None]:
        for child in marko_paragraph.children:
            if isinstance(child, extended_markdown.Image):
                if child.dest.startswith("http://") or child.dest.startswith("https://"):
                    full_path = child.dest
                else:
                    full_path = os.path.abspath(os.path.expanduser(os.path.join(relative_path_dir, child.dest)))
                yield elements.Image(Caption(child.id or uuid4().hex, [Run(child.title)] if child.title else None), full_path)

    @staticmethod
    def _create_runs(children, classes: list[type] = None, url=None):
        if not classes:
            classes = []
        for child in children:
            if isinstance(child, (extended_markdown.RawText, extended_markdown.Literal)):
                yield Run(child.children,
                          bold=extended_markdown.StrongEmphasis in classes or None,
                          italic=extended_markdown.Emphasis in classes or None,
                          strike_through=extended_markdown.Strikethrough in classes or None,
                          url=url)
            elif isinstance(child, extended_markdown.CodeSpan):
                yield Run(child.children, italic=True)
            elif isinstance(child, extended_markdown.LineBreak):
                yield Run(" ")
            elif isinstance(child, extended_markdown.Image):
                pass  # ignore
            elif isinstance(child, extended_markdown.Reference):
                yield Run("?", reference_target=child.target_id)
            elif isinstance(child, extended_markdown.InlineEquation):
                yield Run(child.latex_equation, italic=True)
            elif isinstance(child, (extended_markdown.Link, extended_markdown.Url)):
                yield from MarkdownParser._create_runs(child.children, classes, url=child.dest)
            elif isinstance(child, (extended_markdown.Emphasis, extended_markdown.StrongEmphasis,
                                    extended_markdown.Strikethrough)):
                yield from MarkdownParser._create_runs(child.children, classes + [type(child)], url=url)
            else:
                print(f"Can't parse inline {type(child)}", file=sys.stderr)
        yield from []
