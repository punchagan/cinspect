import re
import os
from os.path import expanduser, exists, join
SOURCE_DIR = expanduser(os.getenv('PY_SOURCE_DIR', '~/software/random/cpython'))

import inspect

# TYPE : FILE_PATH : SOURCE

def is_builtin_function(object):
    """ Return True for builtin functions like map, reduce, len, ... """

    return inspect.isbuiltin(object) and map.__module__ == object.__module__

def getsource(object):

    with open(getfile(object)) as f:
        full_source = f.read()

    if is_builtin_function(object):
        function_name = 'builtin_%s' % object.__name__
        pattern = 'static PyObject\s*\*\s*%s\s*\(.*?\)\s*?\n{[\s\S]*?\n}' % function_name
        matches = re.findall(pattern, full_source)
        if len(matches) == 1:
            source = matches[0]
        else:
            for match in matches:
                print match
            raise Exception('Too few or too many definitions...')

    elif inspect.isbuiltin(object):
        if isinstance(object.__self__, type):
            ## fixme: a hack to handle classmethods...
            type_name = object.__self__.__name__
        else:
            type_name = type(object.__self__).__name__
        for name_pattern in ('%s%s', '%s_%s'):
            function_name = name_pattern % (type_name, object.__name__)
            pattern = 'static PyObject \*\W*%s\s*\(\W*.*?\n}' % function_name
            matches = re.findall(pattern, full_source, re.DOTALL)
            if matches:
                break
        if len(matches) == 1:
            source = matches[0]
        else:
            raise Exception('Too few or too many definitions...')

    elif inspect.ismethoddescriptor(object):
        type_name = object.__objclass__.__name__
        for name_pattern in ('%s%s', '%s_%s'):
            function_name = name_pattern % (type_name, object.__name__)
            pattern = 'static PyObject \*\W*%s\s*\(\W*.*?\n}' % function_name
            matches = re.findall(pattern, full_source, re.DOTALL)
            if matches:
                break
        if len(matches) == 1:
            source = matches[0]
        else:
            raise Exception('Too few or too many definitions...')

    return source


def getfile(object):
    if is_builtin_function(object):
        return join(SOURCE_DIR, 'Python', 'bltinmodule.c')

    elif inspect.isbuiltin(object):  # and method on a builtin object?
        # fixme: we could possibly check in types to see if it's really a builtin...
        if isinstance(object.__self__, type):
            ## fixme: a hack to handle classmethods...
            type_name = object.__self__.__name__
        else:
            type_name = type(object.__self__).__name__
        path = join(SOURCE_DIR, 'Objects', '%sobject.c' % type_name)
        if not exists(path):
            raise Exception('Could not find source file - %s!' % path)
        return path

    elif inspect.ismethoddescriptor(object):
        type_name = object.__objclass__.__name__
        path = join(SOURCE_DIR, 'Objects', '%sobject.c' % type_name)
        if not exists(path):
            raise Exception('Could not find source file - %s!' % path)
        return path

    else:
        raise NotImplementedError
