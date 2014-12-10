from __future__ import absolute_import, print_function

# Standard library
import unittest

# Local library
from cinspect.index.serialize import _get_most_similar


class TestVersions(unittest.TestCase):

    def test_most_similar(self):
        # Given
        names = ['index-2.7.3.json', 'index-3.4.json']
        version = '2.7.8'

        # When
        name = _get_most_similar(version, names)

        # Then
        self.assertEqual('index-2.7.3.json', name)
