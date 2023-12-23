import os
from copy import deepcopy

from lxml import etree

import latex2mathml.converter
from lxml.etree import _Element


def latex_to_omml(latex_equation: str) -> _Element:
    try:
        mathml = latex2mathml.converter.convert(latex_equation)
        tree = etree.fromstring(mathml)
        xslt = etree.parse(
            os.path.join(os.path.dirname(__file__), "mml2omml.xsl")
        )
        transform = etree.XSLT(xslt)
        new_dom = transform(tree)
        word_math = new_dom.getroot()
    except Exception:
        raise ValueError(f"Can't parse the formula:\n{latex_equation}")

    return word_math


def inline_omml(omml: _Element):
    omml = deepcopy(omml)

    def new_r_with_t(text):
        r = etree.Element("{http://schemas.openxmlformats.org/officeDocument/2006/math}r", nsmap=nsmap)
        t = etree.Element("{http://schemas.openxmlformats.org/officeDocument/2006/math}t", nsmap=nsmap)
        t.text = text
        r.append(t)
        return r

    nsmap = omml.nsmap

    for fraction in omml.xpath("//m:f", namespaces=nsmap):
        num = fraction.xpath('./m:num', namespaces=nsmap)[0]
        den = fraction.xpath('./m:den', namespaces=nsmap)[0]

        new_elements = []

        if len(num) == 1:
            new_elements += num
        else:
            new_elements.append(new_r_with_t("("))
            new_elements += num
            new_elements.append(new_r_with_t(")"))

        new_elements.append(new_r_with_t("/"))

        if len(den) == 1:
            new_elements += den
        else:
            new_elements.append(new_r_with_t("("))
            new_elements += den
            new_elements.append(new_r_with_t(")"))

        for i in range(len(new_elements)):
            fraction.getparent().insert(fraction.getparent().index(fraction) + i, new_elements[i])
        fraction.getparent().remove(fraction)

    return omml
