import re

from marko import block
from marko.ext.gfm.elements import TableCell


class TableRow(block.BlockElement):
    """A table row element."""

    splitter = re.compile(r"\s*(?<!\\)\|\s*")
    delimiter = re.compile(r":?-+:?")
    virtual = True
    _cells = None
    _is_delimiter = False

    def __init__(self, cells):
        self.children = cells

    @classmethod
    def match(cls, source):
        line = source.next_line()
        if not line or not re.match(r" {,3}\S", line):
            return False
        parts = cls.splitter.split(line.strip())
        if parts and not parts[0]:
            parts.pop(0)
        if parts and not parts[-1]:
            parts.pop()
        if len(parts) < 1:
            return False
        cls._cells = parts
        cls._is_delimiter = all(cls.delimiter.match(cell) for cell in parts)
        return True

    @classmethod
    def parse(cls, source):
        source.consume()
        parent = source.state
        cells = cls._cells[:]
        if len(cells) < parent._num_of_cols:
            cells.extend("" for _ in range(parent._num_of_cols - len(cells)))
        elif len(cells) > parent._num_of_cols:
            cells = cells[: parent._num_of_cols]
        cells = [TableCell(cell) for cell in cells]
        if parent.children:
            for head, cell in zip(parent.children[0].children, cells):
                cell.align = head.align
        return cells



class Table(block.BlockElement):
    """A table element."""

    _num_of_cols = None
    _prefix = ""
    override = True

    @classmethod
    def match(cls, source):
        source.anchor()
        if TableRow.match(source) and not TableRow._is_delimiter:
            if not TableRow.splitter.search(source.next_line()):
                return False
            source.pos = source.match.end()
            num_of_cols = len(TableRow._cells)
            if (
                TableRow.match(source)
                and TableRow._is_delimiter
                and num_of_cols == len(TableRow._cells)
            ):
                cls._num_of_cols = num_of_cols
                lens = [len(x) for x in TableRow._cells]
                proportions = [x/sum(lens) for x in lens]
                TableRow.proportions = proportions
                source.reset()
                return True
        source.reset()
        return False

    @classmethod
    def parse(cls, source):
        rv = cls()
        rv._num_of_cols = cls._num_of_cols
        rv.children = []
        with source.under_state(rv):
            TableRow.match(source)
            header = TableRow(TableRow.parse(source))
            rv.children.append(header)
            TableRow.match(source)
            delimiters = TableRow._cells
            source.consume()
            for d, th in zip(delimiters, header.children):
                stripped_d = d.strip()
                th.header = True
                if stripped_d[0] == ":" and stripped_d[-1] == ":":
                    th.align = "center"
                elif stripped_d[0] == ":":
                    th.align = "left"
                elif stripped_d[-1] == ":":
                    th.align = "right"
            while not source.exhausted:
                for e in source.parser._build_block_element_list():
                    if issubclass(e, (Table, block.Paragraph)):
                        continue
                    if e.match(source):
                        break
                else:
                    if TableRow.match(source):
                        rv.children.append(TableRow(TableRow.parse(source)))
                        continue
                break
        return rv

