from unittest import TestCase

from docx.shared import Cm

from md2gost.elements import Run
from md2gost.renderer.common.font_utils import Font
from md2gost.renderer.common.text_line_breaker import TextLineBreaker
from . import _create_test_document

class TestTextLineBreaker(TestCase):
    def setUp(self):
        self._document, self._max_height, self._max_width = _create_test_document()

    def test(self):
        times14_font = Font.get("Times New Roman", False, False, 14)

        cases = [
            (
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam lacinia fringilla lectus, nec euismod odio convallis sed. Nunc ac libero ultricies, condimentum neque et, fermentum urna. Donec feugiat diam sed nulla rutrum, sit amet accumsan odio tempor. Sed fermentum urna. Donec feugiat diam sed nulla rutrum, sit amet accumsan odio tempor. Sed mattis. In porta convallis ipsum eget dignissim. Ut orci ante, bibendum ut lorem quis, gravida molestie neque. Nulla vitae sapien sed risus gravida elementum non eu lorem. Quisque ac turpis nisl.",
                [
                    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam lacinia fringilla",
                    "lectus, nec euismod odio convallis sed. Nunc ac libero ultricies, condimentum neque et,",
                    "fermentum urna. Donec feugiat diam sed nulla rutrum, sit amet accumsan odio tempor.",
                    "Sed fermentum urna. Donec feugiat diam sed nulla rutrum, sit amet accumsan odio",
                    "tempor. Sed mattis. In porta convallis ipsum eget dignissim. Ut orci ante, bibendum ut",
                    "lorem quis, gravida molestie neque. Nulla vitae sapien sed risus gravida elementum non",
                    "eu lorem. Quisque ac turpis nisl."
                ],
                times14_font
            ),
            (
                "Ordered lists are useful when you want to present items in a specific order. This is additional text for illustration. Ordered lists are useful when you want to present items in a specific order. This is additional text for illustration. Ordered lists are useful when you want to present items in a specific order. This is additional text for illustration.",
                [
                    "Ordered lists are useful when you want to present items in a specific order. This is",
                    "additional text for illustration. Ordered lists are useful when you want to present items",
                    "in a specific order. This is additional text for illustration. Ordered lists are useful when",
                    "you want to present items in a specific order. This is additional text for illustration."
                ],
                times14_font
            )
        ]

        for case in cases:
            with self.subTest(case[0]):
                line_breaker = TextLineBreaker(self._max_width, Cm(1.25), case[2])

                split_lines = [" ".join(["".join([run._text for run in runs]) for runs in line]) for line in line_breaker.split_lines([Run(case[0])])]

                self.assertEqual(split_lines, case[1])