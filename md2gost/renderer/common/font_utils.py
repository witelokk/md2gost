from __future__ import annotations
from sys import platform, exit
import subprocess
import logging

from functools import cache, cached_property
from docx.shared import Length, Pt
from PIL import Image, ImageDraw, ImageFont
from freetype import Face


def __find_font_linux(name: str, bold: bool, italic: bool):
    result = subprocess.run(
        "fc-list", shell=True, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True)

    if result.returncode == 0:
        fonts = \
            [line.split(":") for line in result.stdout.strip().split("\n")]
        fonts = [font for font in fonts if len(font) == 3]
    else:
        logging.log(logging.ERROR, "fc-list not found")
        exit(1)

    for path, names, styles in fonts:
        if (name in names
                and ("Bold" in styles) == bool(bold)
                and ("Italic" in styles) == bool(italic)):
            return path
    raise ValueError(f"Font {name} not found")


def find_font(name: str, bold: bool, italic: bool):
    if not name:
        raise ValueError("Invalid font")
    if platform == "linux":
        return __find_font_linux(name, bold, italic)
    else:
        from matplotlib.font_manager import findfont, FontProperties
        return findfont(FontProperties(
            family=name,
            weight="bold" if bold else "normal",
            style="italic" if italic else "normal"), fallback_to_default=False)


class Font:
    def __init__(self, path: str, size_pt: int):
        self._freetypefont = ImageFont.truetype(path, size_pt)
        self._draw = ImageDraw.Draw(Image.new("RGB", (1000, 1000)))

        self._face = Face(path)
        self._face.set_char_size(int(size_pt * 64))

        # check if is mono
        self._face.load_char("i")
        i_width = self._face.glyph.advance.x
        self._face.load_char("m")
        self._is_mono = i_width == self._face.glyph.advance.x

    @property
    def name(self):
        return self._face.family_name.decode()

    @property
    def bold(self):
        return b"Bold" in self._face.style_name

    @property
    def italic(self):
        return b"Italic" in self._face.style_name

    @property
    def size_pt(self):
        return self._freetypefont.size

    @property
    def is_mono(self):
        return self._is_mono

    def get_text_width(self, text: str) -> Length:
        # if not self._is_mono:
        bbox = self._draw.textbbox((0, 0), text, self._freetypefont)
        return Pt(bbox[2] - bbox[0])
        # else:
        #     return Pt(len(text) * self._face.glyph.advance.x / 64)

    @cached_property
    def line_height(self) -> Length:
        # fix for Courier New
        if "Courier" in str(self._face.family_name) and self._freetypefont.size == 12:
            return Pt(13.62)

        return Pt(self._face.size.height / 64 + 0.1)


    @classmethod
    @cache
    def get(cls, name: str, bold: bool, italic: bool, size_pt: int) -> Font:
        path = find_font(name, bold, italic)
        return cls(path, size_pt)
