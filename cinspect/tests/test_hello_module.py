from __future__ import absolute_import, print_function

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
        cls._build_hello_module()
        cls._add_hello_to_path()
        cls._set_reader_db_path()

        if sys.version_info.major == 2:
            cls._setup_py_2()

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
        import os
        from cinspect.index.writer import Writer
        from cinspect.clang_utils import get_libclang_headers
        os.unlink(cls.db)
        clang_args = get_libclang_headers() + ['-I%s' % cls.python_headers]
        writer = Writer(clang_args=clang_args)
        writer.create(cls.temp_dir)

    @classmethod
    def _set_reader_db_path(cls):
        import cinspect.index.reader as R
        cls.db = join(cls.temp_dir, 'DB')
        R.DEFAULT_PATH = cls.db

    @classmethod
    def _set_writer_db_path(cls):
        import cinspect.index.writer as W
        W.DEFAULT_PATH = cls.db

    @classmethod
    def _setup_py_2(cls):
        import sysconfig
        cls.python_headers = sysconfig.get_config_var('INCLUDEPY')
        cls._set_writer_db_path()
        cls._index_hello_module()


if __name__ == '__main__':
    unittest.main()
