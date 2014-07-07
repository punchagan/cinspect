import re
import os
from os.path import expanduser, exists, join
SOURCE_DIR = expanduser(os.getenv('PY_SOURCE_DIR', '~/software/random/cpython'))

import inspect
from clang_find import get_code_from_file

igetsource = inspect.getsource  # hack to allow patching in, inside IPython

class InspectObject(object):
    """ A simple wrapper around the object we are trying to inspect. """

    def __init__(self, obj):
        self.obj = obj

    def getfile(self):
        return inspect.getfile(self.obj)


class PythonObject(InspectObject):
    pass


class BuiltinFunction(InspectObject):

    def getfile(self):
        if self.module == '__builtin__':
            path = ('Python', 'bltinmodule.c')

        else:
            path = ('Modules', '%smodule.c' % self.module)

        return join(SOURCE_DIR, *path)

    @property
    def module(self):
        return self.obj.__module__


class BuiltinMethod(InspectObject):

    def getfile(self):
        path = join(SOURCE_DIR, 'Objects', '%sobject.c' % self.type_name)
        if not exists(path):
            raise Exception('Could not find source file - %s!' % path)

        return path

    @property
    def type_name(self):
        ## fixme: a hack to handle classmethods...
        if isinstance(self.obj.__self__, type):
            type_name = self.obj.__self__.__name__

        else:
            type_name = type(self.obj.__self__).__name__

        return type_name


class MethodDescriptor(BuiltinMethod):

    @property
    def type_name(self):
        return self.obj.__objclass__.__name__


class Module(InspectObject):

    def __init__(self, obj):
        self.obj = obj

    def getfile(self):
        names = ['%smodule.c', '%s.c']
        for name in names:
            path = join(SOURCE_DIR, 'Modules', name % self.obj.__name__)
            if exists(path):
                break
        else:
            raise Exception('Could not find source file - %s!' % path)

        return path


def get_inspect_object(obj):
    """ Returns the object wrapped in the appropriate InspectObject class. """

    try:
        igetsource(obj)
    except (TypeError, IOError) as e:
        # The code to deal with this case is below
        pass
    else:
        return PythonObject(obj)

    if inspect.isbuiltin(obj):
        if obj.__module__ is None:
            # fixme: we could possibly check in `types` to see if it's really a
            # built-in...
            return BuiltinMethod(obj)
        else:
            # Any builtin/compiled functions ...
            return BuiltinFunction(obj)

    elif inspect.ismethoddescriptor(obj):
        return MethodDescriptor(obj)

    elif inspect.ismodule(obj):
        return Module(obj)

    else:
        raise NotImplementedError


def getfile(obj):
    if not isinstance(obj, InspectObject):
        obj = get_inspect_object(obj)
    return obj.getfile()


def getsource(obj):

    if not isinstance(obj, InspectObject):
        obj = get_inspect_object(obj)

    if isinstance(obj, PythonObject):
        source = igetsource(obj.obj)

    else:
        with open(obj.getfile()) as f:
            full_source = f.read()

        if isinstance(obj, Module):
            source = get_code_from_file(obj.getfile(), None)
        else:
            source = get_code_from_file(obj.getfile(), obj.obj.__name__)

    return source
