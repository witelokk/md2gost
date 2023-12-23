from copy import copy

from docx.shared import Length


class LayoutState:
    def __init__(self, max_height: Length, max_width: Length):
        self.max_height: Length = max_height
        self.max_width: Length = max_width
        self._current_height: Length = Length(0)

    def new_page(self):
        self._current_height += self.remaining_page_height

    @property
    def current_page_height(self):
        return self._current_height % self.max_height

    @property
    def remaining_page_height(self) -> Length:
        return self.max_height - self.current_page_height

    @property
    def page(self):
        return int(self._current_height // self.max_height) + 1

    def add_height(self, height: Length):
        self._current_height += height

    def can_fit_to_page(self, height: Length):
        return height <= self.remaining_page_height
