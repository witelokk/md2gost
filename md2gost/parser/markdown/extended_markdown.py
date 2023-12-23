from marko import Markdown
from marko.ext.gfm import GFM
from marko.helpers import MarkoExtension

# export everything from marko
from marko.block import BlockElement
from marko.block import *
from marko.inline import *
from marko.ext.gfm.elements import *

from .caption import Caption
from .equation import Equation
from .heading import Heading
from .setext_heading import SetextHeading
from .reference import Reference
from .table import Table
from .toc import TOC
from .inline_equation import InlineEquation
from .image import Image

Extension = MarkoExtension(
    elements=[
        Equation,
        Reference,
        Caption,
        Table,
        TOC,
        Heading,
        SetextHeading,
        InlineEquation,
        Image,
    ]
)

markdown = Markdown(extensions=[GFM, Extension])
