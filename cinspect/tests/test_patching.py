from __future__ import absolute_import, print_function

# Standard library
import inspect
import unittest

from cinspect import getfile, getsource


class TestPatching(unittest.TestCase):

    def test_patching_inspect_should_work(self):
        # Given
        inspect.getsource = getsource
        inspect.getfile = getfile

        # When
        t = getfile(unittest)
        s = getsource(unittest.main)

        # Then
        self.assertGreater(len(t), 0)
        self.assertGreater(len(s), 0)
