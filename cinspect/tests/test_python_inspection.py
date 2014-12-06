from __future__ import absolute_import, print_function

# Standard library
import inspect
from os.path import abspath, dirname, exists, join
import tempfile
from shutil import copy, rmtree
import subprocess
import unittest

# 3rd-party library
from nose.plugins.attrib import attr

# Local library
from cinspect import getfile, getsource
from cinspect._types import BuiltinMethod, MethodDescriptor

# Imports for testing
import gc
import audioop

DATA = join(dirname(abspath(__file__)), 'data')


@attr('slow')
class TestPythonInspection(unittest.TestCase):

    #### 'TestCase' protocol ##################################################

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.python_dir = join(cls.temp_dir, 'Python-2.7.8')
        cls.db = join(cls.temp_dir, 'DB')
        cls._set_db_path()
        cls._get_and_extract_python_sources()
        cls._configure_python()
        cls._index_sources()

    @classmethod
    def tearDownClass(cls):
        rmtree(cls.temp_dir)

    #### Tests ################################################################

    def test_should_get_source_for_builtin_functions(self):
        # Given
        functions = self._get_builtin_functions()

        for function in functions:
            # When
            source = getsource(function)

            # Then
            self.assertIsFunction(source)
            self.assertIn(function.__name__, source.splitlines()[1])

    def test_should_get_source_for_builtin_methods(self):
        # Given
        functions = self._get_builtin_methods()

        for function in functions:
            # When
            source = getsource(function)
            type_name = BuiltinMethod(function).type_name

            # Then
            self.assertIsMethod(source, type_name)

    def test_should_get_source_for_method_descriptors(self):
        # Given
        for function in self._get_method_descriptors():
            # When
            source = getsource(function)
            try:
                type_name = MethodDescriptor(function).type_name
            except:
                type_name = BuiltinMethod(function).type_name

            # Then
            self.assertIsMethod(source, type_name)

    def test_should_get_source_for_method_from_any_module(self):
        # Given
        function = gc.collect

        # When/Then
        self.assertIsFunction(getsource(function))

    def test_should_get_file_for_method_from_any_module(self):
        # Given
        function = gc.collect

        # When
        path = getfile(function)

        # Then
        self.assertTrue(path.endswith('gcmodule.c'))

    def test_should_get_source_for_module(self):
        # Given
        module = gc

        # When
        source = getsource(module)

        # Then
        self.assertGreaterEqual(len(source.splitlines()), 1)
        self.assertIn('Reference Cycle Garbage Collection', source)

    def test_should_get_source_for_module_with_longname(self):
        # Given
        module = audioop

        # When
        source = getsource(module)

        # Then
        self.assertGreaterEqual(len(source.splitlines()), 1)
        self.assertIn('peak values', source)

    def test_should_get_source_for_type(self):
        # Given
        types = list, dict, set, str, unicode

        # Given
        for t in types:
            # When/Then
            source = getsource(t)
            name = t.__name__
            type_name = name.capitalize() if name != 'str' else 'String'
            self.assertIn('PyTypeObject Py%s_Type' % type_name.capitalize(), source)
            self.assertIn('"%s"' % name, source)

    def test_should_get_source_for_instance_of_a_type(self):
        # Given
        objects = [], {}, set([])

        # Given
        for obj in objects:
            # When/Then
            source = getsource(obj)
            name = type(obj).__name__
            self.assertIn('PyTypeObject Py%s_Type' % name.capitalize(), source)
            self.assertIn('"%s"' % name, source)

    #### Assertions ###########################################################

    def assertIsFunction(self, source):
        source = source.strip()
        self.assertGreaterEqual(len(source.splitlines()), 1)
        self.assertTrue(source.startswith('static PyObject'))
        self.assertTrue(source.endswith('}'))

    def assertIsMethod(self, source, type_name):
        self.assertIsFunction(source)
        self.assertTrue(source.splitlines()[1].startswith(type_name))

    #### Private protocol #####################################################

    @classmethod
    def _configure_python(cls):
        subprocess.check_call(['./configure'], cwd=cls.python_dir)

    @classmethod
    def _download_python_sources(cls, to_dir):
        url = 'https://www.python.org/ftp/python/2.7.8/Python-2.7.8.tgz'
        # fixme: convert to python?
        subprocess.check_call(['wget', '-c', url], cwd=to_dir)

    @classmethod
    def _get_and_extract_python_sources(cls):
        source = join(DATA, 'Python-2.7.8.tgz')
        if not exists(source):
            cls._download_python_sources(DATA)
        copy(source, cls.temp_dir)
        # fixme: convert to python?
        subprocess.check_call(['tar', '-xzf', 'Python-2.7.8.tgz'], cwd=cls.temp_dir)

    def _get_builtin_functions(self):
        ns = {}
        exec 'from __builtin__ import *' in ns

        return [obj for (name, obj) in ns.iteritems() if inspect.isbuiltin(obj)]

    def _get_builtin_methods(self):
        return [

            getattr(kls(), method_name)

            for kls in (dict, list, set)
            for method_name in dir(kls())

            # fixme: fix code to work for [].__add__
            if not method_name.startswith('_')
        ]

    def _get_method_descriptors(self):
        return [

            getattr(kls, method_name)

            for kls in (dict, list, set)
            for method_name in dir(kls())

            # fixme: fix code to work for [].__add__
            if not method_name.startswith('_')
        ]

    @classmethod
    def _index_sources(cls):
        from cinspect.index.writer import Writer
        from cinspect.clang_utils import get_libclang_headers
        clang_args = get_libclang_headers() + [
            '-I%s' % cls.python_dir,
            '-I%s' % join(cls.python_dir, 'Include')
        ]
        writer = Writer(clang_args=clang_args)
        writer.create(cls.python_dir)

    @classmethod
    def _set_db_path(cls):
        import cinspect.index.reader as R
        import cinspect.index.writer as W
        R.DEFAULT_PATH = W.DEFAULT_PATH = cls.db


if __name__ == '__main__':
    unittest.main()
