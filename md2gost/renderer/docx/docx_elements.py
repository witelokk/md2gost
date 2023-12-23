from copy import deepcopy

from docx.document import Document
from docx.oxml import CT_Tbl, CT_R
from docx.section import Section
from docx.shared import Parented, Length, Twips
from docx.table import Table, _Row, _Cell
from docx.text.run import Run

from md2gost.util import create_oxml_element


__all__ = [
    "create_table",
    "create_table_row",
    "create_table_cell",
]


def create_table(parent: Parented | Document, rows: int, cols, width: Length = None, style="Table Grid"):
    if not width:
        left_margin = Twips(int(
            parent.part.styles["Normal Table"]._element.xpath("w:tblPr/w:tblCellMar/w:left")[0].attrib[
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w"]))
        right_margin = Twips(int(
            parent.part.styles["Normal Table"]._element.xpath("w:tblPr/w:tblCellMar/w:right")[0].attrib[
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w"]))
        sect: Section = parent.part.document.sections[-1]
        width = sect.page_width - sect.left_margin - sect.right_margin + left_margin + right_margin

    table = Table(CT_Tbl.new_tbl(rows, cols, width), parent)
    table.width = width
    table.style = style

    # google docs fix
    borders = parent.part.styles[style]._element.xpath("w:tblPr/w:tblBorders")
    if borders:
        table._tbl.tblPr.append(deepcopy(borders[0]))
    for i in range(rows):
        for j in range(cols):
            cell = table.cell(i, j)
            cell._element.remove(cell.paragraphs[0]._element)
            table.cell(i, j)._element.tcPr.append(create_oxml_element("w:shd", {
                "w:fill": "auto", "w:val": "clear"
            }))

    return table


def create_table_row(parent: Table):
    return _Row(create_oxml_element("w:tr"), parent)


def create_table_cell(parent: _Row, width: Length):
    cell = _Cell(create_oxml_element("w:tc"), parent)
    cell.width = width
    return cell


def create_field_run(text: str, instr_text: str) -> Run:
    r = create_oxml_element("w:r")

    r.append(create_oxml_element("w:fldChar", {
        "w:fldCharType": "begin"
    }))
    r.append(create_oxml_element("w:instrText", {
        "xml:space": "preserve"
    }, instr_text))
    r.append(create_oxml_element("w:fldChar", {
        "w:fldCharType": "separate"
    }))
    t = create_oxml_element("w:t")
    r.append(t)
    if text is not None:
        t.text = text
    r.append(create_oxml_element("w:fldChar", {
        "w:fldCharType": "end"
    }))

    return Run(r, None)

def create_image(parent, path: str):
    pass
