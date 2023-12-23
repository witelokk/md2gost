from copy import deepcopy
from functools import cache, cached_property

from docx.oxml import OxmlElement
from docx.shared import Length
from docx.styles.style import _ParagraphStyle

from md2gost.renderer.common.font_utils import Font


@cache
def get_default_style(part):
    default_style_element = OxmlElement("w:style")
    default_style_element.append(deepcopy(part.styles.element.xpath('w:docDefaults/w:pPrDefault/w:pPr')[0]))
    default_style_element.append(deepcopy(part.styles.element.xpath('w:docDefaults/w:rPrDefault/w:rPr')[0]))
    return _ParagraphStyle(default_style_element)


class InheritedParagraphStyle:
    def __init__(self, part, style):
        self._part = part
        self._styles = [part.styles[style]]
        while self._styles[-1].base_style:
            self._styles.append(self._styles[-1].base_style)
        self._styles.append(get_default_style(part))

    def _get_attribute(self, attribute: str, default=None):
        attrs = attribute.split(".")

        for style in self._styles:
            value = style
            for attr in attrs:
                try:
                    value = getattr(value, attr)
                except AttributeError:
                    value = None
                    continue

            if value is not None:
                return value

        return default

    @staticmethod
    def _create_property(attribute: str, default=None):
        return cached_property(lambda self: self._get_attribute(attribute, default))

    font_size = _create_property("font.size")
    font_name = _create_property("font.name")
    font_bold = _create_property("font.bold")
    font_italic = _create_property("font.italic")
    space_before = _create_property("paragraph_format.space_before", Length(0))
    space_after = _create_property("paragraph_format.space_after", Length(0))
    line_spacing = _create_property("paragraph_format.line_spacing")
    first_line_indent = _create_property("paragraph_format.first_line_indent")
    alignment = _create_property("paragraph_format.alignment")

    @property
    def font(self) -> Font:
        return Font.get(self.font_name, self.font_bold, self.font_italic, self.font_size.pt)

    @cache
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)
