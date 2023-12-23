from io import BytesIO

from docx.document import Document
from docx.oxml.ns import qn
from docx.oxml import CT_P, CT_Tbl, CT_Blip
from docx.styles.style import _ParagraphStyle
from docx.text.paragraph import Paragraph


class DocxAppender:
    """Appends another docx document to `target_document`"""

    def __init__(self, target_document: Document):
        self._document = target_document

    def append(self, other_document: Document):
        # copy element styles to element
        default_style_element = type("DefaultStyle", (), {})
        default_style_element.rPr = \
            other_document.styles.element.xpath(
                'w:docDefaults/w:rPrDefault/w:rPr')[0]
        default_style_element.pPr = \
            other_document.part.document.styles.element.xpath(
                'w:docDefaults/w:pPrDefault/w:pPr')[0]
        default_style = _ParagraphStyle(default_style_element)

        for element in other_document._body._element.iter():
            if isinstance(element, CT_P):
                p = Paragraph(element, other_document)
                styles = [p.style or other_document.styles["Normal"]]
                while styles[-1].base_style:
                    styles.append(styles[-1].base_style)
                styles.append(default_style)

                space_before = None
                space_after = None
                first_line_indent = None
                alignment = None
                line_spacing = None
                page_break_before = None
                keep_together = None
                keep_with_next = None
                left_indent = None
                right_indent = None

                for style in styles[::-1]:
                    if style.paragraph_format.space_before is not None:
                        space_before = style.paragraph_format.space_before
                    if style.paragraph_format.space_after is not None:
                        space_after = style.paragraph_format.space_after
                    if style.paragraph_format.first_line_indent is not None:
                        first_line_indent = style.paragraph_format.first_line_indent
                    if style.paragraph_format.alignment is not None:
                        alignment = style.paragraph_format.alignment
                    if style.paragraph_format.line_spacing is not None:
                        line_spacing = style.paragraph_format.line_spacing
                    if style.paragraph_format.page_break_before is not None:
                        page_break_before = style.paragraph_format.page_break_before
                    if style.paragraph_format.keep_together is not None:
                        keep_together = style.paragraph_format.keep_together
                    if style.paragraph_format.keep_with_next is not None:
                        keep_with_next = style.paragraph_format.keep_with_next
                    if style.paragraph_format.left_indent is not None:
                        left_indent = style.paragraph_format.left_indent
                    if style.paragraph_format.right_indent is not None:
                        right_indent = style.paragraph_format.right_indent

                if p.paragraph_format.space_before is None:
                    p.paragraph_format.space_before = space_before or 0
                if p.paragraph_format.space_after is None:
                    p.paragraph_format.space_after = space_after or 0
                if p.paragraph_format.first_line_indent is None:
                    p.paragraph_format.first_line_indent = first_line_indent or 0
                if p.paragraph_format.alignment is None:
                    p.paragraph_format.alignment = alignment or 0
                if p.paragraph_format.line_spacing is None:
                    p.paragraph_format.line_spacing = line_spacing or 0
                if p.paragraph_format.page_break_before is None:
                    p.paragraph_format.page_break_before = page_break_before or False
                if p.paragraph_format.keep_together is None:
                    p.paragraph_format.keep_together = keep_together or False
                if p.paragraph_format.keep_with_next is None:
                    p.paragraph_format.keep_with_next = keep_with_next or False
                if p.paragraph_format.left_indent is None:
                    p.paragraph_format.left_indent = left_indent or 0
                if p.paragraph_format.right_indent is None:
                    p.paragraph_format.right_indent = right_indent or 0
            elif isinstance(element, CT_Blip):
                r_id = element.attrib[qn("r:embed")]
                image_blob = BytesIO(
                    other_document.part.related_parts[r_id].image.blob)
                r_id, _ = self._document.part.get_or_add_image(image_blob)
                element.set(qn("r:embed"), r_id)

        # copy elements from title to document
        self._document.add_section().is_linked_to_previous = True

        # todo: copy footer

        self._document.sections[1].page_width =\
            self._document.sections[0].page_width
        self._document.sections[1].page_height =\
            self._document.sections[0].page_height
        self._document.sections[1].left_margin =\
            self._document.sections[0].left_margin
        self._document.sections[1].top_margin =\
            self._document.sections[0].top_margin
        self._document.sections[1].right_margin =\
            self._document.sections[0].right_margin
        self._document.sections[1].bottom_margin =\
            self._document.sections[0].bottom_margin

        self._document.sections[0].page_width =\
            other_document.sections[0].page_width
        self._document.sections[0].page_height =\
            other_document.sections[0].page_height
        self._document.sections[0].left_margin =\
            other_document.sections[0].left_margin
        self._document.sections[0].top_margin =\
            other_document.sections[0].top_margin
        self._document.sections[0].right_margin =\
            other_document.sections[0].right_margin
        self._document.sections[0].bottom_margin =\
            other_document.sections[0].bottom_margin

        i = 0
        for element in other_document._body._element.getchildren():
            if isinstance(element, (CT_P, CT_Tbl)):
                self._document._body._element.insert(i, element)
                i += 1

        self._document.sections[-1].footer.is_linked_to_previous = False
