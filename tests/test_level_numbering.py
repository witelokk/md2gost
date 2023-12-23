from unittest import TestCase

from md2gost.renderer.common.level_numbering import LevelNumbering


class TestLevelNumbering(TestCase):
    def test_default(self):
        numbering = LevelNumbering()
        with self.subTest():
            self.assertEqual("1.1.1", numbering.new(3))
        with self.subTest():
            self.assertEqual("1.1.2", numbering.new(3))
        with self.subTest():
            self.assertEqual("1.2", numbering.new(2))
        with self.subTest():
            self.assertEqual("1.2.1", numbering.new(3))
        with self.subTest():
            self.assertEqual("1.2.1.1", numbering.new(4))
        with self.subTest():
            self.assertEqual("1.2.1.2", numbering.new(4))
        with self.subTest():
            self.assertEqual("1.2.1.2.1.1", numbering.new(6))
