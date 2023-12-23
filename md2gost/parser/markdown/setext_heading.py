from marko.block import SetextHeading as SetextHeading_


class SetextHeading(SetextHeading_):
    override = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.numbered = not (self.inline_body[0] == "*")
        if not self.numbered:
            self.inline_body = self.inline_body[1:]
