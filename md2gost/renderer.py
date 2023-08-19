from docx.document import Document
from docx.shared import Length, Cm, Parented, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

from .renderable import Renderable
from .rendered_info import RenderedInfo
from .util import create_element
from .layout_tracker import LayoutTracker


class Renderer:
    """Renders Renderable elements to docx file"""

    def __init__(self, document: Document):
        self._document: Document = document
        max_height = document.sections[0].page_height - document.sections[0].top_margin - Pt(36+15.6)  # todo add bottom margin detection with footer
        max_width = self._document.sections[0].page_width - self._document.sections[0].left_margin\
            - self._document.sections[0].right_margin
        self._layout_tracker = LayoutTracker(max_height, max_width)

        self.previous_rendered = None

        self._to_new_page: list[Renderable] = []

    def process(self, renderables: list[Renderable]):
        # add page numbering to the footer
        paragraph = self._document.sections[0].footer.paragraphs[0]
        paragraph.paragraph_format.first_line_indent = 0
        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        paragraph._p.append(create_element("w:fldSimple", {
            "w:instr": "PAGE \\* MERGEFORMAT"
        }))

        for i in range(len(renderables)):
            if self._layout_tracker.is_new_page:
                self._flush_to_new_screen()

            infos = renderables[i].render(self.previous_rendered, self._layout_tracker.current_state)

            for info in infos:
                if isinstance(info, Renderable):
                    self._to_new_page.append(info)
                else:
                    self._add(info.docx_element, info.height)
                    self.previous_rendered = info

        self._flush_to_new_screen()

    def _flush_to_new_screen(self):
        while self._to_new_page:
            renderable_ = self._to_new_page.pop(0)
            for info_ in renderable_.render(self.previous_rendered, self._layout_tracker.current_state):
                self._add(info_.docx_element, info_.height)

    def _add(self, element: Parented, height: Length):
        self._document._body._element.append(
            element._element
        )
        self._layout_tracker.add_height(height)