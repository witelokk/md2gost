import re

from marko.inline import Image as Image_


class Image(Image_):
    override = True
    def __init__(self, match):
        super().__init__(match)

        self.id = None

        if self.title and (m := re.match(r"\%(\w+)( (.+))?", self.title)):
            self.id = m.group(1)
            self.title = m.group(2)
