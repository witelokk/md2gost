from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from lxml.etree import _Element


def create_oxml_element(name: str, *args: dict[str, str] | list[_Element] | str):
    """Creates an OxmlElement

    Variable arguments:
    * dict -- element's attributes
    * list -- element's children
    * string -- element's text
    """
    attrs = {}
    children = []
    text = None

    for arg in args:
        if isinstance(arg, dict):
            attrs.update(arg)
        elif isinstance(arg, list):
            children.extend(arg)
        elif isinstance(arg, str):
            text = arg

    element = OxmlElement(name, {
        (qn(name) if ":" in name else name): value for name, value in attrs.items()
    })
    for child in children:
        element.append(child)
    if text:
        element.text = text
    return element
