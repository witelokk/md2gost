from docx.shared import Length, Pt
from uniseg.linebreak import line_break_units

from md2gost.elements.paragraph import Paragraph
from md2gost.elements.run import Run
from md2gost.renderer.common.font_utils import Font


class TextLineBreaker:
    def __init__(self, max_width: Length, first_line_indent: Length, font: Font):
        self._max_width = max_width
        self._first_line_indent = first_line_indent

        self._font = font

    def _get_text_width(self, runs: list[Run], start: int, end: int) -> tuple[list[Run], Length]:
        new_runs = []
        width = 0
        pos = 0
        for i, run in enumerate(runs):
            if pos > end:
                return new_runs, Length(width)
            font = self._font.get(self._font.name, self._font.bold or run.bold, self._font.italic or run.italic,
                                 self._font.size_pt)
            if pos + len(run.text) >= start:
                run_text = run.text[max(0, start - pos):end - pos]
                width += font.get_text_width(run_text)
                new_runs.append(Run(run_text, run.bold, run.italic, run.strike_through, run.color, run.url))
            pos += len(run.text)
        return new_runs, Length(width)

    def split_lines(self, runs: list[Run]):
        space_width = self._font.get_text_width(" ")
        if not self._font.is_mono:
            # space_width *= 0.8
            # space_width = self._font.get_text_width("a")
            space_width = Pt(3.45)

        text = "".join([run.text for run in runs])

        def tailor(s, breakables):
            breakables = list(breakables)
            for i in range(1, len(s) - 1):
                if s[i] in ("/",):
                    if s[i - 1] == " ":
                        breakables[i] = 1
                    breakables[i + 1] = 0
                if s[i] in ("$",) and s[i - 1] not in {" ", "-", "—", "–"}:
                    breakables[i] = 0
            return breakables

        line_width = self._first_line_indent or 0
        lines = [[]]
        pos = 0
        for unit in line_break_units(text, tailor=tailor):
            spaces = len(unit) - len(unit.rstrip())
            new_runs, no_spaces_width = self._get_text_width(runs, pos, pos + len(unit) - spaces)
            full_width = no_spaces_width + spaces * space_width
            if no_spaces_width <= self._max_width - line_width:
                line_width += full_width
                lines[-1] += [new_runs]
            elif no_spaces_width > self._max_width:
                if lines[-1] == "":
                    lines.pop(-1)
                i = 0
                for j in range(len(unit) + 1):
                    new_runs, part_width = self._get_text_width(runs, pos + i, pos + j)
                    if not self._font.is_mono:
                        part_width *= 1.001  # word compresses characters
                        # to fit one more character into the line
                    if part_width > (self._max_width if len(lines) != 0 else self._max_width -
                                     (self._first_line_indent or 0)):
                        lines.append(unit[i:j - 1])
                        raise NotImplementedError()  # /\
                        i = j - 1
                lines.append(unit[i:])
                raise NotImplementedError()  # /\
                line_width = self._font._get_text_width(unit[i:])
            else:
                lines.append([new_runs])
                line_width = full_width
            pos += len(unit)

        return lines

