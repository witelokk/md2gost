import sys
from collections.abc import Collection
from copy import deepcopy
from io import BytesIO
from typing import Generator

import docx
import requests
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.oxml import CT_Tbl
from docx.oxml.ns import qn
from docx.shared import Length, StoryChild, Twips, Pt, Mm, RGBColor, Cm
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from docx.document import Document

from md2gost.renderer.renderer import Renderer
from .docx_appender import DocxAppender
from ..common.font_utils import Font
from ..common.level_numbering import LevelNumbering
from ..redering_settings import RenderingSettings
from ..common.inherited_paragraph_style import InheritedParagraphStyle
from ..common.text_line_breaker import TextLineBreaker
from ... import elements
from functools import singledispatchmethod

from .layout_state import LayoutState
from .debugger import Debugger
from md2gost.renderer.docx.docx_elements import create_table, create_field_run
from ...elements import Element
from md2gost.renderer.docx.math.latex_math import latex_to_omml
from ...util import create_oxml_element


class DocxRenderer(Renderer):
    EQUATION_HEIGHT = Pt(50)

    def __init__(self, elements_: Collection[Element], rendering_settings: RenderingSettings, docx_template: Document):
        super().__init__(elements_)

        self._rendering_settings = rendering_settings

        self._docx_template = docx_template
        self._document = deepcopy(self._docx_template)
        self._document._body.clear_content()

        self._debugger = Debugger(self._document) if rendering_settings.debug else None

        self._layout_state = LayoutState(Mm(297 - 20 - 18.6), Mm(210 - 25 - 10))  # get from document
        self._previous_rendered: StoryChild | None = None

        self._toc_paragraphs: dict[int, Paragraph] = {}

    def _render(self):
        # append title
        if self._rendering_settings.title:
            if not self._rendering_settings.title.endswith(".docx"):
                print("Файл титульника должен иметь расширение docx")
                sys.exit(1)
            document_appender = DocxAppender(self._document)
            document_appender.append(docx.Document(self._rendering_settings.title))

        if self._rendering_settings.debug:
            self._debugger = Debugger(self._document)

        # set first page
        self._document._body._element.xpath("w:sectPr/w:pgNumType")[0].set(
            qn("w:start"), str(self._rendering_settings.first_page))

        # add page numbering to the footer
        paragraph = self._document.sections[-1].footer.paragraphs[0]
        paragraph.paragraph_format.first_line_indent = 0
        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        paragraph._p.append(create_oxml_element("w:fldSimple", {
            "w:instr": "PAGE \\* MERGEFORMAT"
        }))

        for element in self._elements:
            for docx_element, height in self._render_element(element):
                if docx_element:
                    self._document._body._element.append(docx_element._element)

                if self._debugger and height:
                    self._debugger.add(docx_element, height)

                self._layout_state.add_height(height)
                self._previous_rendered = docx_element

    def save(self, path: str):
        if self._debugger:
            self._debugger.after_rendered()
        self._document.save(path)

    @singledispatchmethod
    def _render_element(self, element: elements.Element) -> Generator[tuple[StoryChild, Length], None, None]:
        print(f"Can't render {type(element)}", file=sys.stderr)
        yield from []

    @_render_element.register
    def _render_paragraph(self, paragraph: elements.Paragraph):
        docx_paragraph = self._create_paragraph_from_runs(paragraph.runs, "Normal")

        style = InheritedParagraphStyle(self._document.part, "Normal")

        line_breaker = TextLineBreaker(self._layout_state.max_width, style.first_line_indent, style.font)

        yield docx_paragraph, self._calculate_paragraph_height(line_breaker, paragraph.runs, style)

    def _calculate_paragraph_height(self, line_breaker: TextLineBreaker, runs: list[Run],
                                    style: InheritedParagraphStyle) -> Length:
        space_before = style.space_before
        # if isinstance(self._previous_rendered, Table):
        #     space_before = docx_paragraph.paragraph_format.space_before = Mm(3.5)

        if self._layout_state.current_page_height == 0 and self._layout_state.page > 1:
            space_before = 0
        elif isinstance(self._previous_rendered, Paragraph) and self._previous_rendered.paragraph_format.space_after:
            space_before = max(0, space_before - (self._previous_rendered.paragraph_format.space_after or 0))

        lines = len(line_breaker.split_lines(runs))

        height = space_before + lines * style.font.line_height * style.line_spacing + style.space_after
        fitting_lines = 0
        for lines in range(1, lines + 1):
            if (style.space_before + ((lines - 1) * style.line_spacing + 1) * style.font.line_height
                    > self._layout_state.remaining_page_height):
                break
            fitting_lines += 1

        if fitting_lines == lines:
            # the whole paragraph fits page
            height = min(height, self._layout_state.remaining_page_height)
        elif fitting_lines <= 1 or (lines - fitting_lines == 1 and lines == 3):
            # if only no or only one line fits the page, paragraph goes to the next page
            height += self._layout_state.remaining_page_height
        elif lines - fitting_lines == 1:
            # if all lines except last fit the page, the last two lines go to the new page
            height = (self._layout_state.remaining_page_height +
                      style.space_before + style.font.line_height * style.line_spacing * 2
                      + style.space_after)
        else:
            height = (self._layout_state.remaining_page_height +
                      style.space_before + style.font.line_height *
                      (lines - fitting_lines) + style.space_after)

        return Length(height)

    @_render_element.register
    def _render_equation(self, equation: elements.Equation):
        word_math = latex_to_omml(equation.latex)

        sect = self._document.part.document.sections[-1]

        left_margin = Twips(int(self._document.part.styles["Normal Table"]._element
                                .xpath("w:tblPr/w:tblCellMar/w:left")[0].attrib[qn("w:w")]))
        right_margin = Twips(int(self._document.part.styles["Normal Table"]._element
                                 .xpath("w:tblPr/w:tblCellMar/w:right")[0].attrib[qn("w:w")]))

        table_width = sect.page_width - sect.right_margin - sect.left_margin + left_margin + right_margin

        self._table = table = Table(CT_Tbl.new_tbl(1, 2, table_width), self._document)

        left_cell = table.cell(0, 0)
        right_cell = table.cell(0, 1)
        right_cell.width = Pt(30)
        left_cell.width = table_width - right_cell.width

        table.rows[0].height = self.EQUATION_HEIGHT

        left_paragraph = left_cell.paragraphs[0]
        left_paragraph.style = "Formula Content"
        left_paragraph._p.append(word_math)
        left_cell.vertical_alignment = \
            WD_CELL_VERTICAL_ALIGNMENT.CENTER

        right_paragraph = right_cell.paragraphs[0]
        right_paragraph.style = "Formula Numbering"
        right_paragraph._p.append(create_oxml_element("w:r", "("))

        if equation.caption and equation.caption.id:
            right_paragraph._p.append(create_oxml_element("w:bookmarkStart", {
                "w:id": equation.caption.id,
                "w:name": equation.caption.id
            }))
        self._numbering_run = create_oxml_element("w:r", str(self._reference_numbers[equation.caption.id]))
        right_paragraph._p.append(
            create_oxml_element("w:fldSimple", {
                "w:instr": f"SEQ Формула \\* ARABIC"
            }, [self._numbering_run]))
        if equation.caption and equation.caption.id:
            right_paragraph._p.append(create_oxml_element("w:bookmarkEnd", {
                "w:id": equation.caption.id
            }))
        right_paragraph._p.append(create_oxml_element("w:r", ")"))
        right_cell.vertical_alignment = \
            WD_CELL_VERTICAL_ALIGNMENT.CENTER

        height = Pt(50)

        if height > self._layout_state.remaining_page_height:
            height += self._layout_state.remaining_page_height

        yield self._table, height

    @_render_element.register
    def _render_image(self, image: elements.Image):
        paragraph = Paragraph(create_oxml_element("w:p"), self._document)
        paragraph.paragraph_format.space_before = 0
        paragraph.paragraph_format.space_after = 0
        paragraph.paragraph_format.first_line_indent = 0
        paragraph.paragraph_format.line_spacing = 1
        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        try:
            if image.path.startswith("http://") or image.path.startswith("https://"):
                bytesio = BytesIO()
                bytesio.write(requests.get(image.path).content)
                docx_image = paragraph.add_run().add_picture(bytesio)
            else:
                docx_image = paragraph.add_run().add_picture(image.path)
        except (FileNotFoundError, ConnectionError):
            print(f"{image.path} не существует, картинка не будет добавлена")
            yield from []
            return

        def resize(width: Length = None, height: Length = None):
            if not any((width, height)):
                return

            if not width:
                width = height * (docx_image.width / docx_image.height)

            if not height:
                height = width * (docx_image.height / docx_image.width)

            docx_image.width = Length(width)
            docx_image.height = Length(height)

        caption_paragraph, caption_height = self._render_numbered_caption(
            image.caption.id, "Рисунок", image.caption.runs, True)

        # limit width by max width
        if docx_image.width > self._layout_state.max_width:
            resize(width=self._layout_state.max_width)

        # limit height (including caption height) by max height / 3
        if docx_image.height + caption_height > self._layout_state.max_height / 3:
            resize(height=self._layout_state.max_height / 3 - caption_height)

        height = docx_image.height

        if height + caption_height > self._layout_state.remaining_page_height:
            if height * 0.7 <= (self._layout_state.remaining_page_height - caption_height):
                # shrink the image a little, so it fits to the current page
                resize(height=self._layout_state.remaining_page_height - caption_height)
                height = self._layout_state.remaining_page_height - caption_height
            else:
                height += self._layout_state.remaining_page_height
                paragraph.paragraph_format.page_break_before = True

        yield paragraph, height
        yield caption_paragraph, caption_height

    def _render_numbered_caption(self, reference: str, category: str, runs: list[elements.Run], center: bool = False) \
            -> tuple[Paragraph, Length]:
        paragraph = Paragraph(create_oxml_element("w:p"), self._document._body)

        if reference:
            paragraph._p.append(create_oxml_element("w:bookmarkStart", {
                "w:id": reference,
                "w:name": reference
            }))
        paragraph.add_run(category + " ")

        if reference:
            paragraph._p.append(create_oxml_element("w:fldSimple", {
                "w:instr": f"SEQ {category} \\* ARABIC"
            }, [create_oxml_element("w:r", [
                create_oxml_element("w:t", str(self._reference_numbers[reference]))]
                                    )]))

        if runs:
            paragraph.add_run(" — ")
            self._add_runs_to_paragraph(paragraph, runs)

        if reference:
            paragraph._p.append(create_oxml_element("w:bookmarkEnd", {
                "w:id": reference
            }))

        paragraph.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER if center else None
        paragraph.style = "Caption"

        caption_style = InheritedParagraphStyle(self._document.part, "Caption")

        line_breaker_runs = [elements.Run(f"{category} {self._reference_numbers[reference]}")]
        if runs:
            line_breaker_runs.append(elements.Run(" — "))
            line_breaker_runs.extend(runs)

        line_breaker = TextLineBreaker(self._layout_state.max_width, caption_style.first_line_indent,
                                       caption_style.font)

        height = (caption_style.space_before + len(line_breaker.split_lines(line_breaker_runs)) *
                  caption_style.line_spacing * caption_style.font.line_height + caption_style.space_after)

        return paragraph, height

    def _render_caption(self, text: str, center: bool = False, page_break_before=False) -> tuple[Paragraph, Length]:
        paragraph = Paragraph(create_oxml_element("w:p"), self._document._body)

        paragraph.add_run(text)
        paragraph.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER if center else None
        paragraph.style = "Caption"

        if page_break_before:
            paragraph.paragraph_format.page_break_before = True

        caption_style = InheritedParagraphStyle(self._document.part, "Caption")

        line_breaker = TextLineBreaker(self._layout_state.max_width, caption_style.first_line_indent,
                                       caption_style.font)

        height = (caption_style.space_before + len(line_breaker.split_lines([elements.Run(text)])) *
                  caption_style.line_spacing * caption_style.font.line_height + caption_style.space_after)

        return paragraph, height

    @_render_element.register
    def _render_heading(self, heading: elements.Heading):
        paragraph = self._create_paragraph_from_runs(heading.runs, f"Heading {heading.level}")

        paragraph._element.insert(0, create_oxml_element("w:bookmarkStart", {
            "w:id": heading.reference,
            "w:name": heading.reference
        }))
        paragraph._element.append(create_oxml_element("w:bookmarkEnd", {
            "w:id": heading.reference,
        }))

        heading_style = InheritedParagraphStyle(self._document.part, paragraph.style.name)
        if not heading.numbered:  # remove numbering
            paragraph._p.pPr.append(
                create_oxml_element("w:numPr", [
                    create_oxml_element("w:ilvl", {"w:val": "0"}),
                    create_oxml_element("w:numId", {"w:val": "0"})
                ])
            )
            paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        if heading.level == 1 and not (self._layout_state.page == 1 and self._layout_state.current_page_height == 0):
            paragraph.paragraph_format.page_break_before = True

        space_before = heading_style.space_before

        # add space before if the previous element is table
        if isinstance(self._previous_rendered, Table):
            space_before = paragraph.paragraph_format.space_before = Mm(3.5)

        if (self._layout_state.current_page_height == 0 and self._layout_state.page != 1) \
                or paragraph.paragraph_format.page_break_before:
            space_before = 0

        paragraph.paragraph_format.space_before = space_before

        line_breaker = TextLineBreaker(self._layout_state.max_width, heading_style.first_line_indent+Cm(1.25),
                                       heading_style.font)

        lines = len(line_breaker.split_lines(heading.runs))
        height = (space_before + lines * heading_style.font.line_height * heading_style.line_spacing +
                  heading_style.space_after)

        # if a heading + 3 lines don't fit to the page, it goes to the next page
        if heading_style.space_before + (
                (lines + 3 - 1) * heading_style.line_spacing + 1) * heading_style.font.line_height \
                > self._layout_state.remaining_page_height:
            paragraph.paragraph_format.space_before = 0  # libreoffice fix
            height -= max(heading_style.space_before - (self._previous_paragraph_space_after or 0), 0)

            # force this behaviour as there could be a table or an image instead of a paragraph
            paragraph.paragraph_format.page_break_before = True

        if paragraph.paragraph_format.page_break_before:
            yield None, self._layout_state.remaining_page_height

        yield paragraph, Length(height)

        # set page in toc
        if id(heading) in self._toc_paragraphs:
            self._toc_paragraphs[id(heading)].add_run(str(self._layout_state.page))

    @property
    def _previous_paragraph_space_after(self) -> Length:
        if not isinstance(self._previous_rendered, Paragraph):
            return Length(0)

        return InheritedParagraphStyle(self._document.part, self._previous_rendered.style.name).space_after \
            or self._previous_rendered.paragraph_format.space_after

    @_render_element.register
    def _render_list(self, list_: elements.List, level: int = 0):
        number = 1
        for item in list_.items:
            for i, element in enumerate(item.elements):
                if isinstance(element, (elements.Paragraph, elements.Heading)):
                    if i == 0:
                        marker = f"{number}." if list_.ordered else "●"
                        number += 1
                    else:
                        marker = ""
                    yield from self._render_list_paragraph(element, level, marker)
                elif isinstance(element, elements.List):
                    yield from self._render_list(element, level + 1)
                else:
                    yield from self._render_element(element)

    def _render_list_paragraph(self, paragraph: elements.Paragraph | elements.Heading, level: int, marker: str = ""):
        docx_paragraph = Paragraph(create_oxml_element("w:p"), self._document)

        docx_paragraph.add_run(marker + "\t")
        self._add_runs_to_paragraph(docx_paragraph, paragraph.runs)

        normal_style = InheritedParagraphStyle(self._document.part, "Normal")

        # first level indent is a first_line_indent of normal text
        first_indent = normal_style.first_line_indent
        indent = (first_indent or 0) + Twips(425) * level

        # idk how it works but it works
        tab_size = Twips(360)
        docx_paragraph.paragraph_format.tab_stops.add_tab_stop(tab_size)
        docx_paragraph.paragraph_format.left_indent = (Twips(425) + indent)
        docx_paragraph.paragraph_format.first_line_indent = -Twips(425)

        line_breaker = TextLineBreaker(self._layout_state.max_width - Cm(2),# indent - tab_size,
                                       Length(0), normal_style.font)

        yield docx_paragraph, self._calculate_paragraph_height(line_breaker, paragraph.runs, normal_style)

    @_render_element.register
    def render_listing(self, listing: elements.Listing):
        caption_paragraph, caption_height = \
            self._render_numbered_caption(listing.caption.id, "Листинг", listing.caption.runs)

        code_style = InheritedParagraphStyle(self._document.part, "Code")

        line_height = Font.get(code_style.font_name, code_style.font_bold, code_style.font_italic,
                               code_style.font_size.pt).line_height * code_style.line_spacing

        code_lines = []
        for code_line in listing.get_lines(self._rendering_settings.syntax_highlighting):
            line_breaker = TextLineBreaker(self._layout_state.max_width, code_style.first_line_indent,
                                           code_style.font)
            code_lines.append((code_line, len(line_breaker.split_lines(code_line))))

        full_lines = sum(lines for runs, lines in code_lines)

        # if 2 lines of code won't fit the page, move everything to the new page
        if (caption_height + line_height * 2 > self._layout_state.remaining_page_height and
                caption_height + full_lines * line_height > self._layout_state.remaining_page_height):
            caption_paragraph.paragraph_format.page_break_before = True
            caption_height += self._layout_state.remaining_page_height

        yield caption_paragraph, caption_height

        table = create_table(self._document, 1, 1)
        for runs, lines in code_lines:
            if line_height * lines > self._layout_state.remaining_page_height:
                yield table, Pt(1)  # borders
                yield None, self._layout_state.remaining_page_height
                table = create_table(self._document, 1, 1)

                yield self._render_caption(f"Продолжение листинга {self._reference_numbers[listing.caption.id]}",
                                           page_break_before=True)

            paragraph = table.cell(0, 0).add_paragraph(style="Code")
            for run in runs:
                docx_run = paragraph.add_run()
                docx_run.text = run.text
                docx_run.bold = run.bold
                docx_run.italic = run.italic
                if run.color:
                    docx_run.font.color.rgb = RGBColor.from_string(run.color)

            yield None, line_height * lines
        yield table, Pt(1)  # borders

    @_render_element.register
    def _render_table(self, table: elements.Table):
        docx_table = create_table(self._document, 0, table.cols_count)
        docx_table.autofit = False

        rows = []
        for i, row in enumerate(table.rows):
            row_height = 0
            for j, cell in enumerate(row.cells):
                cell_height = 0
                for element in cell.items:
                    if isinstance(element, elements.Paragraph):
                        table_text_style = InheritedParagraphStyle(self._document.part, "Table Text")

                        line_breaker = TextLineBreaker(docx_table.width / table.cols_count - Mm(1.9 * 2),
                                                       table_text_style.first_line_indent, table_text_style.font)

                        # debug line splitting
                        # lines = text_sizer.split_lines()
                        # for line in lines:
                        #     line_text = ""
                        #     for part in line:
                        #         line_text += "".join(run.text for run in part) + " "
                        #     print(line_text)
                        # print("\n\n")

                        cell_height += (table_text_style.space_before + table_text_style.space_after +
                                        len(line_breaker.split_lines(element.runs)) *
                                        table_text_style.line_spacing * table_text_style.font.line_height)
                    elif isinstance(element, elements.Image):
                        pass
                    else:
                        raise NotImplementedError(type(element))
                row_height = max(row_height, cell_height)
            rows.append((row, row_height))

        caption, caption_height = self._render_numbered_caption(table.caption.id, "Таблица", table.caption.runs)
        if caption_height + rows[0][1] > self._layout_state.remaining_page_height:
            caption_height += self._layout_state.remaining_page_height
            caption.paragraph_format.page_break_before = True

        yield caption, caption_height

        for row, row_height in rows:
            if row_height > self._layout_state.remaining_page_height:
                yield docx_table, 0
                docx_table = create_table(self._document, 0, table.cols_count)
                docx_table.autofit = False

                yield None, self._layout_state.remaining_page_height
                caption, caption_height = self._render_caption(
                    f"Продолжение таблицы  {self._reference_numbers[table.caption.id]}", page_break_before=True)
                caption.paragraph_format.page_break_before = True
                yield caption, caption_height

            docx_row = docx_table.add_row()

            for i, docx_cell in enumerate(docx_row.cells):
                if i < len(row.cells):
                    docx_cell._element.clear()  # remove empty paragraph
                    docx_cell.width = Pt(50)
                    for element in row.cells[i].items:
                        if isinstance(element, elements.Paragraph):
                            paragraph = self._create_paragraph_from_runs(element.runs, "Table Text")
                            paragraph.paragraph_format.alignment = {
                                "left": WD_PARAGRAPH_ALIGNMENT.LEFT,
                                "justify": WD_PARAGRAPH_ALIGNMENT.JUSTIFY,
                                "center": WD_PARAGRAPH_ALIGNMENT.CENTER,
                                "right": WD_PARAGRAPH_ALIGNMENT.RIGHT
                            }[row.cells[i].alignment]
                            docx_cell._element.append(paragraph._element)
                else:
                    docx_cell.paragraphs[0].style = "Table Text"
            yield None, row_height + Pt(0.5)

        yield docx_table, 0

    @_render_element.register
    def _render_toc(self, _: elements.TOC):
        numbering = LevelNumbering()
        for heading in self._headings:
            docx_paragraph = Paragraph(create_oxml_element("w:p"), self._document)
            docx_paragraph.paragraph_format.tab_stops.add_tab_stop(
                self._document.sections[-1].page_width -
                self._document.sections[-1].left_margin - self._document.sections[-1].right_margin,
                alignment=WD_TAB_ALIGNMENT.RIGHT, leader=WD_TAB_LEADER.DOTS)
            docx_paragraph.paragraph_format.tab_stops.add_tab_stop(0, alignment=WD_TAB_ALIGNMENT.LEFT,
                                                                   leader=WD_TAB_LEADER.SPACES)
            docx_paragraph.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
            docx_paragraph.paragraph_format.first_line_indent = 0

            text = (('\u00A0' * 4 * (heading.level - 1) + numbering.new(
                heading.level) + '  ' if heading.numbered else '')
                    + heading.text)
            hyperlink = create_oxml_element("w:hyperlink")
            hyperlink.append(create_oxml_element("w:r", [
                create_oxml_element("w:t", text),
                create_oxml_element("w:tab")
            ]))
            hyperlink.set(qn("w:anchor"), heading.reference)
            docx_paragraph._element.append(hyperlink)
            style = InheritedParagraphStyle(self._document.part, "Normal")

            line_breaker = TextLineBreaker(self._layout_state.max_width, Length(0), style.font)

            self._toc_paragraphs[id(heading)] = docx_paragraph

            yield docx_paragraph, self._calculate_paragraph_height(line_breaker, [elements.Run(heading.text)], style)

    def _create_paragraph_from_runs(self, runs: list[elements.Run], style: str) -> Paragraph:
        paragraph = Paragraph(create_oxml_element("w:p"), self._document)
        paragraph.style = style

        self._add_runs_to_paragraph(paragraph, runs)

        return paragraph

    def _add_runs_to_paragraph(self, paragraph: Paragraph, runs: list[elements.Run]):
        for run in runs:
            if run.reference_target:
                if run.reference_target in self._reference_numbers:
                    number = self._reference_numbers[run.reference_target]
                else:
                    number = "?"
                docx_run = create_field_run(str(number), f"REF {run.reference_target} \\h")
                paragraph._element.append(docx_run._element)
            elif run.url:
                hyperlink = create_oxml_element("w:hyperlink")
                if run.url.startswith("#"):
                    hyperlink.set(qn("w:anchor"), run.url.removeprefix("#"))
                else:
                    r_id = self._document.part.relate_to(run.url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
                    hyperlink.set(qn("r:id"), r_id)
                paragraph._element.append(hyperlink)
                docx_run = Run(create_oxml_element("w:r"), paragraph)
                docx_run.style = "Hyperlink"
                hyperlink.append(docx_run._element)
                docx_run.text = run.text
            else:
                docx_run = paragraph.add_run(run.text)
            docx_run.bold = run.bold
            docx_run.italic = run.italic
            docx_run.font.strike = run.strike_through

    def _fill_toc(self):
        pass
