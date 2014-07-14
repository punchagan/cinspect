from __future__ import absolute_import, print_function

# Standard library
import inspect
from os.path import join
import tempfile
from shutil import rmtree
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

# fixme: the index can be messed up, causing the tests to fail.  We should use
# our own index.  But, this would take very long!

# fixme: Should we run tests on a dummy module of our own, not cpython?


@attr(speed='slow')
class TestPythonInspection(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.python_dir = join(cls.temp_dir, 'Python-2.7.8')
        cls.db = join(cls.temp_dir, 'DB')
        cls._monkey_patch()
        cls._download_and_extract_python_sources()
        cls._build_python()
        cls._index_sources()

    # fixme: think of a better name, if not a better way of doing this.
    @classmethod
    def _monkey_patch(cls):
        import cinspect.index.reader as R
        import cinspect.index.writer as W
        R.DEFAULT_PATH = W.DEFAULT_PATH = cls.db

    @classmethod
    def _download_and_extract_python_sources(cls):
        url = 'https://www.python.org/ftp/python/2.7.8/Python-2.7.8.tgz'
        commands = [
            ['wget', '-c', url],
            ['tar', '-xzf', 'Python-2.7.8.tgz'],
        ]

        for command in commands:
            subprocess.check_call(command, cwd=cls.temp_dir)

    @classmethod
    def _build_python(cls):
        commands = [
            ['./configure'],
            # ['make'],
        ]

        for command in commands:
            subprocess.check_call(command, cwd=cls.python_dir)

    @classmethod
    def _index_sources(cls):
        from cinspect.index.writer import Writer
        clang_args = [
            '-I%s' % cls.python_dir,
            '-I%s' % join(cls.python_dir, 'Include')
        ]
        # fixme: gottu remove this!
        clang_args.insert(0, '-I/usr/lib/clang/3.5/include')
        writer = Writer(clang_args=clang_args)
        writer.create(cls.python_dir)

    @classmethod
    def _(cls):
        url = 'https://www.python.org/ftp/python/2.7.8/Python-2.7.8.tgz'
        command = ['wget', '-c', url]
        subprocess.check_call(command, cwd=cls.temp_dir)

    @classmethod
    def tearDownClass(cls):
        rmtree(cls.temp_dir)

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


if __name__ == '__main__':
    unittest.main()
