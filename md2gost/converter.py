import os.path
import sys
from typing import Collection

from docx import Document

from .parser import create_parser_by_extension
from .renderer import create_renderer_by_extension
from .renderer.redering_settings import RenderingSettings


class Converter:
    def __init__(self, template_path: str, title_path: str | None, first_page: int, debug: bool, syntax_highlighting: bool):
        self._template = Document(template_path)
        self._rendering_settings = RenderingSettings(
            debug=debug, syntax_highlighting=syntax_highlighting, title=title_path, first_page=first_page)

    def convert(self, input_paths: Collection[str], output_path: str):
        output_extension = output_path.split(".")[-1]

        elements = []
        for input_path in input_paths:
            extension = input_path.split(".")[-1]
            parser = create_parser_by_extension(extension)

            if not parser:
                print(f"Формат {extension} не поддерживается!", file=sys.stderr)
                sys.exit(1)

            with open(input_path, "r", encoding="utf-8") as f:
                elements += parser.parse(f.read(), os.path.dirname(input_path))

        renderer = create_renderer_by_extension(output_extension, elements, self._rendering_settings, self._template)
        if not renderer:
            print(f"Формат {output_extension} не поддерживается!", file=sys.stderr)
            sys.exit(1)

        renderer.render()
        renderer.save(output_path)
