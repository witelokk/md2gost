from collections.abc import Collection

from docx.document import Document

from .renderer import Renderer
from .docx import DocxRenderer
from .redering_settings import RenderingSettings
from ..elements import Element


def create_renderer_by_extension(extension: str, elements: Collection[Element],
                                 rendering_settings: RenderingSettings, docx_template: Document) -> Renderer | None:
    """
    Creates a suitable renderer for file based on its extension.
    :return: Initialized parser if possible, otherwise None
    """

    if extension == "docx":
        return DocxRenderer(elements, rendering_settings, docx_template)

    return None
