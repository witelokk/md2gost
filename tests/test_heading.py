from unittest import TestCase

from md2gost.elements import Heading


class TestHeading(TestCase):
    def test_link_reference(self):
        heading = Heading()
        heading.add_run("Hello world, Привет Мир 123412 !!! _@$&#$")
        self.assertEqual("hello-world-привет-мир-123412--_", heading.reference)
