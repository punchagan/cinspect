from __future__ import absolute_import, print_function

import sys
import unittest
if sys.version_info.major > 2:
    raise unittest.SkipTest('Indexing is only supported in Py2.x')

# Standard library
from os.path import abspath, dirname, join
import tempfile
import re
from shutil import copytree, rmtree
import subprocess
import sys
import unittest

# Local library
from cinspect import getsource


class TestHelloModule(unittest.TestCase):

    #### 'TestCase' protocol ##################################################

    @classmethod
    def setUpClass(cls):
        cls.hello_dir = join(dirname(abspath(__file__)), 'data')
        cls.temp_dir = tempfile.mktemp()
        cls.db = join(cls.temp_dir, 'DB')
        cls.python_headers = '/usr/include/python2.7/'
        cls._set_db_path()
        cls._build_hello_module()
        cls._add_hello_to_path()
        cls._index_hello_module()

    @classmethod
    def tearDownClass(cls):
        rmtree(cls.temp_dir)

    #### Tests ################################################################

    def test_should_get_source_for_say_hello(self):
        # Given
        import hello

        # When
        source = getsource(hello.say_hello)

        # Then
        self.assertEqual(
            source.strip(), self._get_code_from_hello_module("say_hello")
        )

    def test_should_get_source_for_hello_module(self):
        # Given
        import hello

        # When
        source = getsource(hello)

        # Then
        self.assertEqual(source, self._get_code_from_hello_module())

    # fixme: add tests for methods, type definitions, ...

    #### Private protocol #####################################################

    @classmethod
    def _add_hello_to_path(cls):
        sys.path.insert(0, cls.temp_dir)

    @classmethod
    def _build_hello_module(cls):
        copytree(cls.hello_dir, cls.temp_dir)
        subprocess.check_call(
            ['python', 'setup.py', '-q', 'build_ext', '--inplace'], cwd=cls.temp_dir
        )

    def _get_code_from_hello_module(self, name=None):
        """ Return code that is labelled with the given name. """

        with open(join(self.hello_dir, 'hellomodule.c')) as f:
            text = f.read()

        if name is None:
            code = text

        else:
            pattern = "//.*start:.*{name}((.|\s)+?)//.*end:.*{name}"
            matches = re.search(pattern.format(name=name), text)
            code = matches.groups()[0].strip() if matches is not None else ''

        return code

    @classmethod
    def _index_hello_module(cls):
        from cinspect.index.writer import Writer
        from cinspect.clang_utils import get_libclang_headers
        clang_args = get_libclang_headers() + ['-I%s' % cls.python_headers]
        writer = Writer(clang_args=clang_args)
        writer.create(cls.temp_dir)

    @classmethod
    def _set_db_path(cls):
        import cinspect.index.reader as R
        import cinspect.index.writer as W
        R.DEFAULT_PATH = W.DEFAULT_PATH = cls.db


if __name__ == '__main__':
    unittest.main()
