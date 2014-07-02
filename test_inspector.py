import inspect
import unittest
import gc

from cinspect import getsource


class TestGetSource(unittest.TestCase):

    def test_should_get_source_for_builtin_functions(self):
        # Given
        for function in self._get_builtin_functions():
            # When/Then
            self.assertPyMethodDef(getsource(function))

    def test_should_get_source_for_builtin_methods(self):
        # Given
        for function in self._get_builtin_methods():
            # When/Then
            self.assertPyMethodDef(getsource(function))

    def test_should_get_source_for_method_descriptors(self):
        # Given
        for function in self._get_method_descriptors():
            # When/Then
            self.assertPyMethodDef(getsource(function))

    def test_should_get_source_for_compiled_method(self):
        # Given
        function = gc.collect

        # When/Then
        self.assertPyMethodDef(getsource(function))

    def test_should_get_source_for_module(self):
        # Given
        module = gc

        # When
        source = getsource(module)

        # Then
        self.assertGreaterEqual(len(source.splitlines()), 1)
        self.assertIn('Reference Cycle Garbage Collection', source)

    #### Assertions ###########################################################

    def assertPyMethodDef(self, source):
        source_lines = source.splitlines()
        self.assertGreaterEqual(source_lines, 1)
        self.assertNotIn('\nstatic PyObject', '\n'.join(source_lines[2:]))

    #### Private protocol #####################################################

    def _get_builtin_functions(self):
        builtin_functions = []
        ns = {}
        exec 'from __builtin__ import *' in ns

        return [obj for (name, obj) in ns.iteritems() if inspect.isbuiltin(obj)]

    def _get_builtin_methods(self):
        return [

            getattr(kls(), method_name)

            for kls in (list, set, dict)
            for method_name in dir(kls())

            # fixme: fix code to work for {}.view*
            if not method_name.startswith(('_', 'view'))
        ]

    def _get_method_descriptors(self):
        return [

            getattr(kls, method_name)

            for kls in (list, set, dict)
            for method_name in dir(kls())

            # fixme: fix code to work for dict.view*
            if not method_name.startswith(('_', 'view'))
        ]


if __name__ == '__main__':
    unittest.main()
